FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive
COPY server server
COPY service_account service_account
RUN chmod +x server/install.sh && ./server/install.sh
EXPOSE 3000
CMD ["/bin/bash", "./server/run.sh"]