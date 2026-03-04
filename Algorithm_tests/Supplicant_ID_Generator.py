#Class used to generate a supplicant_ID

class Supplicant_Manager():

    
    def __init__(self, initial_id) -> None:
        self._initialid_=initial_id
        self._supplicantid_=initial_id
        self._max_allowed_ids_=99999



    #Name:generate_supplicant_id
    #generates a supplicant_id (previous supplicant id +1)
    #Parameters: None
    #return: self._supplicantid_ [attribute of the class object]
    def generate_supplicant_id(self):

        self._supplicantid_=self._supplicantid_+1

        if self._supplicantid_> self._max_allowed_ids_:
            self.restart_supplicant()

        return self._supplicantid_



    #Name:restart_supplicant
    #supplicant id to the number defined as _initialid_
    #Parameters: None
    #return: self._supplicantid_ [attribute of the class object]
    def restart_supplicant(self):
        self._supplicantid_=self._initialid_


if __name__ == '__main__':

    mysupplicantmanager=Supplicant_Manager(0)
    for l in range (0,50):
        supplicant_id=mysupplicantmanager.generate_supplicant_id()
        print (supplicant_id)
