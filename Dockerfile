FROM ubuntu:20.04

# setup timezone
ENV TZ=UTC

# setup dependencies versions

ENV FFMPEG_version=4.2.2 \
	VMAF_version=1.5.1 \
	easyVmaf_version=1.1 

# get and install building tools
WORKDIR     /tmp/workdir
RUN \
	ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
	apt-get update -yqq && \
	apt-get install --no-install-recommends\
		ninja-build \
		python3 \
		python3-pip \
		python3-setuptools \
		python3-wheel \
		ninja-build \
		wget \
		doxygen \
		autoconf \
		automake \
		cmake \
		g++ \
		gcc \
		pkg-config \
		make \
		nasm \
		yasm -y && \
	apt-get autoremove -y && \
    apt-get clean -y && \
	pip3 install --user meson && \
	rm -rf /tmp/workdir

# install libvmaf
WORKDIR     /tmp/workdir
RUN \
	export PATH="${HOME}/.local/bin:${PATH}" && \
	echo $PATH &&\
	wget https://github.com/Netflix/vmaf/archive/v${VMAF_version}.tar.gz && \
	tar -xzf  v${VMAF_version}.tar.gz && \
	cd vmaf-${VMAF_version}/libvmaf/ && \
	meson build --buildtype release && \
	ninja -vC build && \
	ninja -vC build test && \
	ninja -vC build install && \
	rm -rf /tmp/workdir

# install ffmpeg
WORKDIR     /tmp/workdir
RUN \
	export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/local/lib64/" && \
	export PKG_CONFIG_PATH="${PKG_CONFIG_PATH}:/usr/local/lib64/pkgconfig/" && \
	wget https://ffmpeg.org/releases/ffmpeg-${FFMPEG_version}.tar.bz2 && \
	tar xjf ffmpeg-${FFMPEG_version}.tar.bz2 && \
	cd ffmpeg-${FFMPEG_version} && \
	./configure --enable-libvmaf --enable-version3 --disable-shared && \
	make && \
	make install && \
	rm -rf /tmp/workdir

ENV LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/local/lib64/"
# install  easyVmaf
WORKDIR  /app
RUN \
	wget https://github.com/gdavila/easyVmaf/archive/v${easyVmaf_version}.tar.gz && \
	tar -xzf  v${easyVmaf_version}.tar.gz

# app setup
WORKDIR  /app/easyVmaf-${easyVmaf_version}
ENTRYPOINT [ "python3", "easyVmaf.py" ]
