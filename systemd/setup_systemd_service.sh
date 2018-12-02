#!/bin/bash

cd ..

./build.sh

# Generate service description

echo -e "[Unit]
Description= instance
After=network.target

[Service]
User=$(whoami)
Group=$(whoami)
WorkingDirectory=$(pwd)
Environment=\"PATH=/usr/bin\"
ExecStart=$(pwd)/out/PyMusicServer3 -s $(pwd)/resources/settings.cfg -l debug

[Install]
WantedBy=multi-user.target
" > systemd/PyMusicServer3.service

# Enable and start service
sudo cp systemd/PyMusicServer3.service /etc/systemd/system/
sudo systemctl start PyMusicServer3
sudo systemctl enable PyMusicServer3