#AttendedScore.py

#:::DESCRIPTION:::
# This script defines the algorithm to calculate the attended score, which is used by the decision maker to
# determine when to attend a task with issues. Once a decision has been taken, the attended score is set based on a given policy 
# This score will decrease each DM iteration (value of decreament given by the user).
# This approach is used in order to give time to the system to apply changes (i.e. pes change). 
# So it can be considered as a time buffer after which, if the task is still facing issues, 
# the DM component will attempt to serve it again. The attended score avoids the issue of attending several times
# the same task and not giving time to the system to check how the new pes performs.


#Name:setPolicyBasedScore
#applies polymorphism so whenever we want to communicate with any component, we send the 
#object, and generic paramentes
#Parameters: **kwargs
 #return: specific communicate method based on object type

def setPolicyBasedScore (object, **kwargs):

    return object.setPolicyBasedScore(**kwargs)



class PriorityPolicy():
    def __init__(self) -> None:
        self._MAX_SCORE_=6

    def setPolicyBasedScore(self, **kwargs):
        #print("message from priority based policy")
        score=int(self._MAX_SCORE_/int(kwargs["_priority_"])+1)

        return score


class WeightedPolicy():
    def __init__(self) -> None:
        self._MAX_SCORE_=10


    def setPolicyBasedScore(self, **kwargs):
        #print("message from weighted based policy")
        score=int(self._MAX_SCORE_/int(kwargs["_priority_"])) + 5

        return score




class AttendedScoreManager():
    def __init__(self, policy) -> None:
        self._ATTENDED_SCORE_VALUE=1
        self._MAX_ATTENDED_SCORE_VALUE=5
        self._MIN_ATTENDED_SCORE_VALUE=0
        self.policy=policy
        if self.policy=="priority":
            self.policy_score_manager=PriorityPolicy()
        elif self.policy=="weighted":
            self.policy_score_manager=WeightedPolicy()            
        else: 
            print ("no policy found")
            self.policy_score_manager=PriorityPolicy()


    def setPolicyBasedScore (self, **kwargs):
        score=setPolicyBasedScore (self.policy_score_manager, **kwargs)
        return score



    #Name:increaseAttendedScore
    #increases AttendedScore by _ATTENDED_SCORE_VALUE.
    #Parameters: score[int]
    #return: score[int] 

    def increaseAttendedScore(self, score, value=-1000):
        if value==-1000:
            value=self._ATTENDED_SCORE_VALUE
        if (score>=self._MAX_ATTENDED_SCORE_VALUE):
            score=self._MAX_ATTENDED_SCORE_VALUE
        else:
            score=score+value
        
        return score



    #Name:decreaseAttendedScore
    #decreases AttendedScore by _ATTENDED_SCORE_VALUE.
    #Parameters: score[int]
    #return: score[int] 

    def decreaseAttendedScore(self, score, value=-1000):
        if value==-1000:
            value=self._ATTENDED_SCORE_VALUE
        if (score<=self._MIN_ATTENDED_SCORE_VALUE):
            score=self._MIN_ATTENDED_SCORE_VALUE
        else:
            score=score-value
        
        return score





if __name__ == '__main__':
    obj=AttendedScoreManager("priority")#sets _issues_data to default param to get the system started
    score=obj.setPolicyBasedScore(_priority_=5)
    print ("calculated score: ",score )
    obj2=AttendedScoreManager("weighted")#sets _issues_data to default param to get the system started
    score2=obj2.setPolicyBasedScore(_priority_=1)
    print ("calculated score: ",score2 )

    score=obj.decreaseAttendedScore(score)
    print ("decreased score: ",score )

    
  



        




