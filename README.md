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

#### General Settings

- obsws_host -> URL or IP address of your OBS instance
- obsws_port -> port on which the OBS-Websocket plugin is listening
- obsws_pass -> password for the OBS-Websocket plugin

- stream_dwell_time -> time in seconds for which a stream stays active before switching to another
- enable_obs_alive_check -> enable checking weather obs is running and streaming and restart if possible ( currently only works on linux)
- enable_secrecy -> if your are printing stuff that is intellectual property of someone else, enable a mode to not activate a stream if a certain catchphrase is present int the filename
- secrecy_catchphrase -> secrecy catchphrase, if this string is found in the filename of the printjob, the video feed will not be shown
- disable_after_finish_time -> time in seconds after which a finished print is not displayed anymore

#### Add a new entry to the pStream.yaml in the "instances" section

Each instance has four parameters
- name -> name of the instance, used for displaying in the overlay and identification of the scene
- url -> url of the OctoPrint instance, supports url´s, ip addresses and multicast dns names
- apikey -> OctoPrint Api Key for accessing the print status
- forceactive -> boolean flag to show the stream regardless of the print status

Example:

>name: "Prusa i3"
>url: "http://prusa.local"
>apikey: "F95E1544CF248AAAEFC49460CFB9E43"
>forceactive: True

#### Configure OBS-Studio
I won´t go into detail here on how to properly setup OBS, just a few things.

- Add a new scene to OBS, make sure its name matches the "name" entered in the pStream.yaml
- to this scene, add a media source with according to the example in the picture, make sure to use the right url e.g. {octoprint-url}:8080/?action=stream

[OBSsource]: https://github.com/pkElectronics/OctoPrintSutdio/raw/master/doc/source.PNG "Source Setup"

- add two text Freetype2 text sources named {name}.text1 and {name}.text2 and position them in the scene. (those a deprecated as of v26, but well, I don´t care)
- repeat the steps for every OctoPrint Instance you´d like to control
- add a scene named "IDLE" and configure it as you wish

[OBSoverview]: https://github.com/pkElectronics/OctoPrintSutdio/raw/master/doc/overview.PNG "OBS Overview"

Should look something like this when you´re done.

