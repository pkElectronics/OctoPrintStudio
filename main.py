# This is a sample Python script.

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import asyncio
import subprocess

import yaml

from concurrent.futures.process import ProcessPoolExecutor

import simpleobsws
from octorest import OctoRest
import time
import os

loop = asyncio.get_event_loop()
p = ProcessPoolExecutor(2)  # Create a ProcessPool with 2 processes
ws = None
streamDwellTime = 10  # seconds
enableObsAliveCheck = True
enableSecrecy = True
secrecyCatchphrase = "geheim"
disableAfterFinishTime = 600
octoprintObsInstances = []


class OctoPrintObsInstance:
    lastStateChange = 0
    lastActivation = 0

    jobInfo = None
    printer = None
    printing = False
    descriptionText1 = ""
    descriptionText2 = ""

    def __init__(self, url, apikey, scene, printing_forced=True):
        self.url = url
        self.apikey = apikey
        self.scene = scene
        self.printing_forced = printing_forced

    def is_secret(self):
        if not enableSecrecy:
            return False

        if self.jobInfo is None:
            return False
        if self.jobInfo['job']['file']['name'] is None:
            return False
        return secrecyCatchphrase in self.jobInfo['job']['file']['name']

    def is_printing(self):
        return self.printing_forced | self.printing

    def generate_info_text(self):
        # [ Printer: Tronxy | File: abcde.gcode | Progress: 19% ] /r/n [ Bed Temp: 50°C / 60°C | E0 Temp 50°C / 60°C ]
        if not self.jobInfo is None and not self.printer is None:
            self.descriptionText1 = "[ Printer: "
            self.descriptionText1 += self.scene
            self.descriptionText1 += " | File: "
            self.descriptionText1 += self.jobInfo['job']['file']['name'] if not self.jobInfo['job']['file'][
                                                                                    'name'] is None else "-"
            self.descriptionText1 += " | Progress: "
            self.descriptionText1 += '{:03.2f}'.format(self.jobInfo['progress']['completion']) if not \
                self.jobInfo['progress']['completion'] is None else "- "
            self.descriptionText1 += "% ]"
            self.descriptionText2 = "[ Bed Temp: "
            self.descriptionText2 += '{:03.1f}'.format(self.printer['temperature']['bed']['actual'])
            self.descriptionText2 += "°C / "
            self.descriptionText2 += '{:03.1f}'.format(self.printer['temperature']['bed']['target'])
            self.descriptionText2 += "°C | E0 Temp "
            self.descriptionText2 += '{:03.1f}'.format(self.printer['temperature']['tool0']['actual'])
            self.descriptionText2 += "°C / "
            self.descriptionText2 += '{:03.1f}'.format(self.printer['temperature']['tool0']['target'])
            self.descriptionText2 += "°C "

            if 'tool1' in self.printer['temperature']:
                self.descriptionText2 += "| E1 Temp "
                self.descriptionText2 += '{:03.1f}'.format(self.printer['temperature']['tool1']['actual'])
                self.descriptionText2 += "°C / "
                self.descriptionText2 += '{:03.1f}'.format(self.printer['temperature']['tool1']['target'])
                self.descriptionText2 += "°C "
            self.descriptionText2 += "]"

        else:
            self.descriptionText1 = "[default]"
            self.descriptionText2 = "[default]"


async def switch_to_scene(sceneName):
    try:
        print("Switching Scene to:" + sceneName)
        data = {'scene-name': sceneName}
        await ws.call('SetCurrentScene', data)  # Make a request with the given data
    except Exception as e:
        print(e)


async def obs_set_scene_text(instance):
    try:
        data = {'source': instance.scene + ".text1", 'text': instance.descriptionText1}
        await ws.call('SetTextFreetype2Properties', data)  # Make a request with the given data
        data = {'source': instance.scene + ".text2", 'text': instance.descriptionText2}
        await ws.call('SetTextFreetype2Properties', data)  # Make a request with the given data
    except Exception as e:
        print(e)


async def obs_alive_check():
    try:
        await ws.call("GetVersion")
    except Exception:
        stream = os.popen('pidof obs')
        output = stream.read()
        print("OBS Pid: " + output)
        if output == "":
            print("obs crashed, restarting...")
            try:
                subprocess.Popen("obs", stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                print("windows it is")
        else:
            try:
                await ws.connect()
            except:
                print("reconnect failed")


async def obs_auto_recconnect_stream():
    try:
        result = await ws.call('GetStreamingStatus')  # Make a request with the given data
        print("Streaming status:")
        print(result)
        if not result["streaming"]:
            print("reconnect stream")
            await ws.call("StartStreaming")

    except Exception as e:
        print(e)


def make_client(url, apikey):
    """Creates and returns an instance of the OctoRest client.

    Args:
        url - the url to the OctoPrint server
        apikey - the apikey from the OctoPrint server found in settings
    """
    try:
        client = OctoRest(url=url, apikey=apikey)
        return client
    except Exception as ex:
        # Handle exception as you wish
        print(ex)


async def run_octoprint_handler():


    activeInstance = None
    activeSince = 0

    while 1:
        for inst in octoprintObsInstances:
            try:
                octoClient = make_client(inst.url, inst.apikey)
                job_info = octoClient.job_info()
                printer = octoClient.printer()

                printing = printer['state']['flags']['printing']

                if inst.printing != printing:
                    inst.printing = printing
                    inst.lastStateChange = time.time()
                inst.jobInfo = job_info
                inst.printer = printer
                inst.generate_info_text()
                await obs_set_scene_text(inst)
            except Exception as e:
                print("Octoprint Connection failed " + inst.scene)
                inst.printing = False


        await asyncio.sleep(1)

        if activeInstance is None:
            for inst in octoprintObsInstances:
                if inst.is_printing():
                    activeInstance = inst
                    activeSince = time.time()
                    inst.lastActivation = activeSince
                    await switch_to_scene(inst.scene)
                    break

            if activeInstance is None:
                await switch_to_scene("IDLE")
        else:
            possibleAlternativeInstances = []
            if time.time() - activeSince > streamDwellTime:
                for inst in octoprintObsInstances:
                    if inst != activeInstance and (
                            inst.is_printing() or (time.time() - inst.lastStateChange < disableAfterFinishTime)) and not inst.is_secret():
                        possibleAlternativeInstances.append(inst)

                if len(possibleAlternativeInstances) == 1:
                    activeInstance = possibleAlternativeInstances[0]
                    activeSince = time.time()
                    activeInstance.lastActivation = activeSince
                    await switch_to_scene(activeInstance.scene)
                elif len(possibleAlternativeInstances) == 0:
                    activeSince = time.time()
                else:
                    candidate = None
                    for inst in possibleAlternativeInstances:
                        if candidate is None:
                            candidate = inst
                        elif inst.lastActivation < candidate.lastActivation:
                            candidate = inst

                    activeInstance = candidate
                    activeSince = time.time()
                    activeInstance.lastActivation = activeSince
                    await switch_to_scene(activeInstance.scene)

        await asyncio.sleep(1)


async def run_obs_checkup():
    while 1:
        await obs_alive_check()
        await obs_auto_recconnect_stream()
        await asyncio.sleep(1)


async def main():
    try:
        await ws.connect()
    except Exception as e:
        print("nop")

    if enableObsAliveCheck:
        loop.create_task(run_obs_checkup())

    loop.create_task(run_octoprint_handler())
    while 1:
        await asyncio.sleep(1)

if __name__ == '__main__':
    with open('pStream.yaml', 'r') as stream:
        data_loaded = yaml.safe_load(stream)

    obsws_host = data_loaded["pStreamConfig"]["obsws_host"]
    obsws_port = data_loaded["pStreamConfig"]["obsws_port"]
    obsws_pw = data_loaded["pStreamConfig"]["obsws_pass"]

    streamDwellTime = data_loaded["pStreamConfig"]["stream_dwell_time"]
    enableObsAliveCheck = data_loaded["pStreamConfig"]["enable_obs_alive_check"]
    enableSecrecy = data_loaded["pStreamConfig"]["enable_secrecy"]
    secrecyCatchphrase = data_loaded["pStreamConfig"]["secrecy_catchphrase"]
    disableAfterFinishTime = data_loaded["pStreamConfig"]["disable_after_finish_time"]

#  OctoPrintObsInstance('http://e3tpu.fritz.box', 'E0A746EC72764B929620E9315EC20203', 'E3TPU'),
#   OctoPrintObsInstance('http://e3ultra.fritz.box', 'EFF054BC9D9B4638AB023615E29AF165', 'E3ULTRA'),
#    OctoPrintObsInstance('http://tronxy.fritz.box', 'F95E1544CF248AAAEFC49460CFB9E43', 'TRONXY')]

    for inst in data_loaded["pStreamConfig"]["instances"]:
        octoprintObsInstances.append(OctoPrintObsInstance(inst["url"], inst["apikey"], inst["name"], inst["forceactive"]))

    ws = simpleobsws.obsws(host=obsws_host, port=obsws_port, password=obsws_pw,
                      loop=loop)  # Every possible argument has been passed, but none are required. See lib code for defaults.

    if data_loaded is not None:
        loop.run_until_complete(main())
