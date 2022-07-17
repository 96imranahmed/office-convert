from ast import arg
from lib2to3.pytree import convert
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from pathlib import Path
import os
import uuid
import aiofiles
import asyncio
import shutil 
import sys
import time
import subprocess as _ , shlex
from unoserver import converter

TEMP_PATH = os.path.abspath(Path("./temp"))
SPLIT_STR = ","
DOCKER_HOST = os.uname().nodename

SupportedTargetTypes = set(["pdf"])

SupportedMimeTypes = {
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/pdf": "pdf",
}
ReverseSupportedMimeTypes = dict((v, k) for k, v in SupportedMimeTypes.items())

time.sleep(2) # Ensure the socket is ready before starting the API server (otherwise results in a race)
app = FastAPI()
libre_converter = converter.UnoConverter(port = "2002")

def create_temp_folder_if_not_exists():
    if not os.path.isdir(TEMP_PATH):
        os.makedirs(TEMP_PATH)

def clean_temp_files(input, output):
    if input and os.path.exists(input):
        os.remove(input)
    if output and os.path.exists(output):
        os.remove(output)

# Delete all temp files on docker restart - TODO: Remove
if os.path.exists(TEMP_PATH):
    shutil.rmtree(TEMP_PATH) 

@app.post("/convert")
async def read_upload(file: UploadFile = File(...), targetType: str = Form()):
    if targetType not in SupportedTargetTypes:
        raise HTTPException(
            status_code=400, detail="targetType `{}` not supported".format(targetType)
        )
    if file.content_type is None or len(file.content_type) == 0:
        raise HTTPException(status_code=400, detail="No file provided")
    if file.content_type not in SupportedMimeTypes:
        raise HTTPException(
            status_code=400,
            detail="Input files of MIMEType `{}` not supported".format(file.content_type),
        )
    if file.content_type == ReverseSupportedMimeTypes[targetType]:
        raise HTTPException(
            status_code=400,
            detail="Input files type and target file type are the same".format(
                file.content_type
            ),
        )
    create_temp_folder_if_not_exists()  # Create temp folder if not exists
    filename_uuid = uuid.uuid4().hex  # Create a temp file name
    filename_original = file.filename
    cache_filepath_input = "{}/{}.{}".format(
        TEMP_PATH, filename_uuid, SupportedMimeTypes[file.content_type]
    )
    cache_filepath_output = "{}/{}.{}".format(
        TEMP_PATH, filename_uuid, targetType
    )

    file_content = await file.read() #

    ## Save to a temp file
    # async with aiofiles.open(
    #     cache_filepath_input,
    #     "wb",
    # ) as out_file:
    #     content = file_content
    #     await out_file.write(content)

    try:
        await asyncio.get_event_loop().run_in_executor(executor=None, func=lambda: libre_converter.convert(indata = file_content, outpath= cache_filepath_output))
        ## Or, process via cmd call
        # cmd = "{} -m unoserver.converter --port 2002 {} {}".format(sys.executable, cache_filepath_input, cache_filepath_output)
        # proc = await asyncio.create_subprocess_exec(*shlex.split(cmd), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        # _ , stderr = await proc.communicate()
        # retcode = proc.returncode
        # if retcode != 0:
        #     raise ValueError("Libreoffice conversion failed with exit code {}".format(retcode))
        clean_temp_files(cache_filepath_input, None) # TODO: Do something with PDF output
        return {
            'file': cache_filepath_output,
            'extract_cmd': 'docker cp {}:{} . && open {}.{}'.format(DOCKER_HOST, cache_filepath_output, filename_uuid, targetType)
        }
    except BaseException as ex:
        clean_temp_files(cache_filepath_input, cache_filepath_output) # Delete any tracked cached files
        raise HTTPException(
            status_code=400,
            detail="Internal server error - error details: {}".format(str(ex)),
        )
