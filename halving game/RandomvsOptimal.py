import random
import matplotlib.pyplot as plt

def choose_random():
  num = random.randint(1,3)
  if num == 1:
    return "divide"
  else:
    return "minus"
  

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
    global optimal_wins
    global random_wins
    if state == 0:
      if self.p1turn:
        print("Optimal Bot Wins!")
        optimal_wins += 1
      else:
        print("Random Win!")
        random_wins += 1
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
    global rand_turns
    global opt_turns
    state = random.randint(15, 50)
    while self.isEnd(state) == False:

      if self.p1turn:
        print("Random turn! Current Number is", state)
        move = choose_random()
        ins = move
        print("Random Bot chooses", ins)
        rand_turns += 1
      else:
        opt_turns+=1
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
        print("Optimal Bot chooses", ins)

      state = self.actions(state, ins)
      if self.p1turn:
        self.p1turn = False
      else:
        self.p1turn = True

#simulation part
random_wins = 0
optimal_wins = 0

list_of_moves = []
for i in range(100):
    rand_turns = 0
    opt_turns = 0
    g = game()
    g.start()
    list_of_moves.append((opt_turns, rand_turns))

print("random bot win", random_wins)
print("optimal bot win", optimal_wins)
print("avg amount of turns per game for rand: ", (rand_turns/100))
print("avg turns pergame for opt is " , opt_turns/100)



#visuals
#pie chart of win rate for minimax vs random

# Labels and values
labels = ['Random bot wins', 'Optimal bot wins']
values = [random_wins, optimal_wins]

# Make the pie chart
# plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
# plt.title("random bot wins vs optimal bot wins")
# plt.show()


list_of_rand = []
list_of_opt = []
for i in list_of_moves:
  list_of_opt.append(i[0])
  list_of_rand.append(i[1])

#make the histogram for optimal bot
# plt.hist(list_of_opt, bins=10, edgecolor='black')

# Label axes
plt.xlabel('Optimal bot move count')
plt.ylabel('Frequency')
plt.title('Optimal bot moves count histogram')
plt.show()

#make histogram for random bot
plt.hist(list_of_rand, bins=9, edgecolor='black')

# Label axes
plt.xlabel('Random bot move count')
plt.ylabel('Frequency')
plt.title('Random bot moves count histogram')

# Show the plot
plt.show()