#!/bin/bash

if [ "$UID" -ne 0 ]
  then echo "This script must be run as root"
  exit
fi

mkdir ./phase/opt/
mkdir ./phase/opt/phase/

echo "Clearing Old Files"
rm -rf ./phase/opt/phase/*

echo "Copying Latest Build"
cp -r ../bash ./phase/opt/phase/
cp -r ../libmproxy ./phase/opt/phase/
cp -r ../libphase ./phase/opt/phase/
cp -r ../netlib ./phase/opt/phase/
cp -r ../phase.glade ./phase/opt/phase/
cp -r ../phase.py ./phase/opt/phase/
cp -r ../resources ./phase/opt/phase/
cp -r ../plugins ./phase/opt/phase/


echo "Building Control File"
cp ./control ./phase/DEBIAN/control
du=`/usr/bin/du -c ./phase/opt/ ./phase/usr/ | grep total | cut -f1`
echo -e "Installed-Size: $du\n" >> ./phase/DEBIAN/control

echo "Removing Binary Python and Temporary Files"
find ./ -name "*~" -exec rm {} \;
find ./ -name *.pyc -exec rm {} \;

echo "Chowning Files"
chown -R root:root ./phase
chmod 755 ./phase/DEBIAN/postinst
chmod 755 ./phase/DEBIAN/postrm


echo "Building Debian File"
dpkg-deb --build phase

echo "Done"
