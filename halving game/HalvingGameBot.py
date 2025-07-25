import random


def pickOptimal(num, mx):
  if num == 0:
    if mx == 0:
      return 1000
    else:
      return -1000
    
  if mx:
    return max(pickOptimal(num - 1, not mx), pickOptimal(num // 2, not mx))
  else:
    return min(pickOptimal(num - 1, not mx), pickOptimal(num // 2, not mx))
    
class game:
  def __init__(self):
    self.begin = random.randint(1, 50)
    self.p1turn = True

  def isEnd(self, state):
    if state == 0:
      if self.p1turn:
        print("Bot Wins!")
      else:
        print("You Win!")
      return True
    else:
      return False

  def actions(self, state, action):
    if action == "divide":
      state = state // 2
    if action == "minus":
      state = state - 1
    return state

  def start(self):
    state = random.randint(15, 50)
    while self.isEnd(state) == False:

      if self.p1turn:
        print("Your turn! Current Number is", state)
        ins = input()
        while ins != "divide" and ins != "minus":
          print("Invalid! Try again!")
          ins = input()
      else:
        print("Bot's turn! Current Number is", state)
        # bot chooses optimal move
        # current_bot_winning = False
        # if pickOptimal(state, False):
        #   current_bot_winning = True
        # print(current_bot_winning)
        minus_val = pickOptimal(state - 1, True)
        divide_val = pickOptimal(state // 2, True)
        if divide_val <= minus_val:
          ins = "divide"
        else:
          ins = "minus"
        print("Bot chooses", ins)

      state = self.actions(state, ins)
      if self.p1turn:
        self.p1turn = False
      else:
        self.p1turn = True
#################################
g = game()
g.start()