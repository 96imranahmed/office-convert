echo "Starting libreoffice / unoserver installation"
apt-get update && \
apt-get install -y libreoffice python3-pip uvicorn && \
apt-get -y -q remove libreoffice-gnome && \
apt -y autoremove 
echo "Successfully installed libreoffice; installing unoserver"
pip install unoserver fastapi "uvicorn[standard]" pydantic python-multipart aiofiles