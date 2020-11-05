# OctoPrintStudio - Work in progress

Simple Toolkit to control the video streams of several OctoPrint instances and output them via OBS-Studio. This tool uses the OctoPrint Rest API to access
information about the current print and adds them as overlay to the video stream. It is also capable of handling multiple instances at once and switch between their respective
streams based on printing progress and activity.
It also checks weather the OBS-Studio instance is still alive and restarts OBS if necessary and reconnects the stream (linux only)

## Dependencies

### Python 3

- PyYAML
- simpleobsws
- octorest

### OBS-Studio
- OBS-Studio (link)
- OBS-Websocket (link)



### Setup & Configuration

The initial setup consists of two necessary steps. First, add the OctoPrint instance to the pStream.yaml to enable access by the script. Second, configure a scene in OBS containing the stream and two text sources

After installing OBS and the OBS-Websocket Plugin, make sure to configure OBS for Streaming to your favourite streaming service and enable the OBS-Websocket Plugin according to the
manuals on their websites. After that perform following steps for each OctoPrint Instance you like to control.

1. Add a new entry to the pStream.yaml in the "instances" section

-
  name: "Prusa i3"
  url: "http://prusa.local"
  apikey: "F95E1544CF248AAAEFC49460CFB9E43"
  forceactive: True
