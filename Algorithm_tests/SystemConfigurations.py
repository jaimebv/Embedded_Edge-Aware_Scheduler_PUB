#SystemConfigurations.py

#:::DESCRIPTION:::
#set all configuration variables of the Embedded-Edge-Aware Agent
class DecisionMakerConfig():

    issue_flag_states=["issue_not_meeting_deadline"] #static variable-- possible states cannot change in runtime
    DMTMcommunication_functions=["get issues","clean issues", "set issues"]
    DMECMcommunication_functions=["open supplicant", "cancel supplicant", "get related supplicant", "get supplicant by id", "complete supplicant", "drop connection" ]
    DMTIcommunication_functions=["migrate task", "suspend task", "resume task"]
    DMSIcommunication_functions=["suspend task", "resume task"]

    def __init__(self) -> None:
        pass

class TaskMonitorConfig():

    issue_flag_states=["issue_not_meeting_deadline", "issue_timeout","issue_resources", "issue_task_suspended"] #static variable-- possible states cannot change in runtime
    task_types=["local", "native", "enhanced"] #static variable-- possible states cannot change in runtime
    def __init__(self) -> None:
        pass

class ECMConfig():

    def __init__(self) -> None:
        pass


class EmbeddedDeviceConfig():

    def __init__(self) -> None:
        #put here embedded device IP
        self._endpoint_="http://192.168.1.101:80/"

    def getPesUpdateEndpoint(self):
        endpoint=self._endpoint_+"pes-update/"

        return endpoint

    def getSuspendTaskEndpoint(self, **kwargs):
        endpoint=self._endpoint_+"suspend-task/"+kwargs["_task_id_"]+"_"+kwargs["_task_part_"]

        return endpoint

    def getResumeTaskEndpoint(self):
        endpoint=self._endpoint_+"resume-task/"

        return endpoint


if __name__ == '__main__':
    obj=EmbeddedDeviceConfig()

    print(obj.getPesUpdateEndpoint())
    print(obj.getSuspendTaskEndpoint(_task_id_="t1", _task_part_="client"))
    print(obj.getSuspendTaskEndpoint(_task_id_="t1", _task_part_="server"))
    print(obj.getResumeTaskEndpoint())