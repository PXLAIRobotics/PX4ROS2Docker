# syntax=docker/dockerfile:1
FROM ubuntu:24.04@sha256:68ee22004a9109b44973313b02ff7b1de250f1de0f5ecb628d73f579aaff33ac AS toolchain
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 ROS_DISTRO=jazzy GZ_DISTRO=harmonic
COPY versions.env /etc/px4-versions.env
COPY docker/install-stack.sh docker/px4-requirements.txt /tmp/
RUN bash /tmp/install-stack.sh && rm /tmp/install-stack.sh /tmp/px4-requirements.txt
COPY docker/install-agent.sh docker/install-qgc.sh /tmp/
RUN bash /tmp/install-agent.sh && rm /tmp/install-agent.sh
# Extraction runs as root; make its root-only top-level directory readable to user.
RUN bash /tmp/install-qgc.sh && chmod -R a+rX /opt/qgroundcontrol && rm /tmp/install-qgc.sh

FROM toolchain AS native
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
# Keep Python numerical packages compatible with Noble/ROS binary extensions.
COPY docker/python-constraints.txt /tmp/python-constraints.txt
RUN /opt/px4-venv/bin/pip install --no-cache-dir -r /tmp/python-constraints.txt \
    && /opt/px4-venv/bin/pip freeze > /etc/px4-python-resolved.txt
# Command-T's Vim-compatible release needs Vim's embedded Ruby support.
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends vim-nox \
    && dpkg-query -W > /etc/px4-packages.txt && rm -rf /var/lib/apt/lists/*
ARG USER_UID=1000
ARG USER_GID=1000
RUN if id ubuntu &>/dev/null; then userdel -r ubuntu; fi \
    && test "$USER_UID" -gt 0 && test "$USER_GID" -gt 0 \
    && (getent group "$USER_GID" || groupadd -g "$USER_GID" user) \
    && useradd -l -m -s /bin/bash -u "$USER_UID" -g "$USER_GID" user \
    && echo 'user ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/developer \
    && chmod 440 /etc/sudoers.d/developer
ENV HOME=/home/user PATH=/home/user/bin:/opt/px4-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
COPY docker/supervise.py /usr/local/lib/px4-supervise.py
COPY docker/bashrc /etc/px4-dev.bashrc
COPY docker/entrypoint.sh /usr/local/bin/px4-entrypoint
COPY docker/install-user-config.sh /usr/local/bin/install-user-config
COPY docker/plugins.lock /etc/px4-plugins.lock
COPY --chown=user docker/tmux.conf /home/user/.tmux.conf
COPY --chown=user docker/vimrc /home/user/.vimrc
COPY docker/rviz-persistent-settings /etc/px4-rviz-settings
COPY docker/fonts /usr/local/share/fonts/cascadia
# Keep HOME literal in .bash_profile so it expands when the user opens a shell.
# hadolint ignore=SC2016
RUN mkdir -p "$HOME"/{bin,Projects,ExampleCode,Data,.rviz2} \
    && cp /etc/px4-rviz-settings "$HOME/.rviz2/persistent_settings" \
    && echo 'source /etc/px4-dev.bashrc' >> "$HOME/.bashrc" \
    && echo 'source "$HOME/.bashrc"' > "$HOME/.bash_profile" \
    && chown -R user:"$(id -gn user)" "$HOME" \
    && chmod +x /usr/local/bin/{px4-entrypoint,install-user-config} \
    && fc-cache -f
USER user
RUN install-user-config
COPY --chown=user Commands/bin /opt/px4-seed/bin
COPY --chown=user Projects/ros2_workspace/src /opt/px4-seed/ros2-src
COPY --chown=user ExampleCode /opt/px4-seed/ExampleCode
RUN cp -a /opt/px4-seed/bin/. "$HOME/bin/" && cp -a /opt/px4-seed/ExampleCode/. "$HOME/ExampleCode/"
WORKDIR /home/user
COPY --chown=user tests /opt/px4-tests
ENTRYPOINT ["/usr/bin/tini", "-g", "--", "/usr/local/bin/px4-entrypoint"]
CMD ["bash"]

FROM native AS vnc
USER root
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    xfce4 xfce4-terminal dbus-x11 tigervnc-standalone-server tigervnc-tools novnc websockify x11-utils \
    && dpkg-query -W > /etc/px4-packages.txt \
    && rm -rf /var/lib/apt/lists/*
COPY --chown=user docker/xfce-terminalrc /home/user/.config/xfce4/terminal/terminalrc
COPY docker/start-vnc.sh /usr/local/bin/start-px4-vnc
COPY docker/qgroundcontrol.desktop /usr/share/applications/qgroundcontrol.desktop
RUN chmod +x /usr/local/bin/start-px4-vnc
USER user
ENV DISPLAY=:1
EXPOSE 5901 6901
CMD ["/usr/local/bin/start-px4-vnc"]
