#!/bin/bash

# requires blkid and grep to be in path
DESTBASE=/media/ubuntu/3e56f669-6b78-45af-a1c6-c506303f43bb/copies
MOUNTBASE=/media/ubuntu
DRIVE=/dev/sr1
COUNTER="0"

if [ ! -d "${DESTBASE}" ]; then
  echo "Can't find destination dir $DESTBASE..."
  exit 1
fi

DISCNAME=`blkid -o value -s LABEL $DRIVE`
echo "Debug: DISCNAME is $DISCNAME"

if [ -d "${DESTBASE}/${DISCNAME}" ]; then
  echo "Debug: Entering while counter"
  while [ -d "${DESTBASE}/${DISCNAME}_${COUNTER}" ]	
  do
    COUNTER=$[$COUNTER+1]
  done
  DEST="${DESTBASE}/${DISCNAME}_${COUNTER}"
else 
  DEST="${DESTBASE}/${DISCNAME}"
fi
echo "Debug: DEST is ${DEST}"

if [ -d "${MOUNTBASE}/${DISCNAME}" ]; then 
  SOURCE="$MOUNTBASE/$DISCNAME"
else
  sudo mkdir -p "/mnt/$DISCNAME"
  Result=$?
  sudo mount $DRIVE "/mnt/$DISCNAME"
  Result=$?
  SOURCE="/mnt/$DISCNAME"
fi
echo "Debug: SOURCE is $SOURCE"

if [ ! -d "${DEST}" ]; then
  echo "Debug: Creating destination directory $DESTINATION"
  mkdir -p "$DEST"
  Result=$?
fi

echo "Beginning copy..."
cp -vr "${SOURCE}" "${DEST}/"
Result=$?
if [ $Result -ne "0" ]; then
  echo "There was an error in the copy... Creating a dd copy for later recovery.."
  dd if=$DRIVE of="${DEST}.iso" bs=2048 conv=noerror,notrunc iflag=nonblock
  Result=$?
  if [ $Result -ne "0" ]; then
    echo "ERROR: dd copy was not sucessful"
  else
    echo "Copy via dd was sucessful"
  fi
else
  echo "Bye bye"
fi
