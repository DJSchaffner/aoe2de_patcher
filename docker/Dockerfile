FROM ubuntu:22.04

WORKDIR /root

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common wget ca-certificates

RUN dpkg --add-architecture i386 && \
	wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key && \
	wget -NP /etc/apt/sources.list.d/ https://dl.winehq.org/wine-builds/ubuntu/dists/jammy/winehq-jammy.sources && \
	apt-add-repository "deb https://dl.winehq.org/wine-builds/ubuntu/ jammy main" && \
	apt update && \
	apt install -y --install-recommends wine-staging-i386=7.20~jammy-1 && \
	apt install -y --install-recommends wine-staging-amd64=7.20~jammy-1 && \
	apt install -y --install-recommends wine-staging=7.20~jammy-1 && \
	apt install -y --install-recommends winehq-staging=7.20~jammy-1

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	dotnet6 \
	gcc \
    patchelf \
	python3-dev \
	python3-pip \
	python3-tk \
    python3-venv \
    xvfb \
    && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt

ENV VIRTUAL_ENV /venv/py3
ENV PATH ${VIRTUAL_ENV}/bin:${PATH}

RUN python3 -m venv ${VIRTUAL_ENV} && \
	pip install -U --no-cache-dir pip setuptools wheel && \
	pip install --no-cache-dir -r /tmp/requirements.txt && \
	rm -f /tmp/requirements.txt

ARG UID
ARG UNAME
ARG GID
RUN groupadd -g ${GID} ${UNAME}
RUN useradd -d /home/${UNAME} -s /bin/bash -m ${UNAME} -u ${UID} -g ${GID}
USER ${UNAME}
ENV HOME /home/${UNAME}
WORKDIR /home/${UNAME}

RUN export WINEDLLOVERRIDES="winemenubuilder.exe,mscoree,mshtml=" && \
	wine reg add 'HKLM\Software\Microsoft\Windows NT\CurrentVersion' /v CurrentVersion /d 10.0 /f && \
	wine reg add 'HKCU\Software\Wine\DllOverrides' /v winemenubuilder.exe /t REG_SZ /d '' /f && \
	wine reg add 'HKCU\Software\Wine\DllOverrides' /v mscoree /t REG_SZ /d '' /f && \
	wine reg add 'HKCU\Software\Wine\DllOverrides' /v mshtml /t REG_SZ /d '' /f && \
	wineserver -w

RUN wget https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.exe && \
	xvfb-run wine python-3.14.3-amd64.exe /passive InstallAllUsers=1 PrependPath=1 && \
	wineserver -w
