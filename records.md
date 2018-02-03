Strength Records
==========

Below records are using the AlphaGoZero way,  which has a 'Evaluator' module. Not AlphaZero way.

Records 1
---------

Rule: Play with this [iOS APP](https://itunes.apple.com/cn/app/id574915961). For each model, we plays 2 games, 1 as black, 1 as white. If wins at least once, no matter as black or white, we count it as a 'won'.

- step-17600 (100sim): won level 1,2,3
- step-20000 (100sim): won level 4
- step-28000 (100sim): won level 5,6,7,8,9,10
- step-40000 (100sim): won level 11
- step-42400 (100sim): won level 12
- step-52000 (100sim): won level 16
- step-54400 (100sim): won level 14,15
- step-56800 (100sim): won level 13
- step-64800 (100sim): lose level 17...
- step-67200 (100sim): lose level 17...
- step-69600 (100sim): lose level 17...
- step-69600 (2000sim): won level 17 (level 18 not tested)

Starting from about step 100000, I change simulations_per_move in selfplay from 100 to 800.

- step-116000 (2000sim): won level 18,19,20,21,22,23,24,25,26,27,28,29,30
- step-116000 (800sim): lose level 29
- step-155200 (2000sim): won level 32 (level 33 not tested)
- step-200800 (800sim): won level 33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50 (level 51 not tested)
- step-200800 (200sim): lose level 51...
- step-200800 (400sim): won level 51,52,53,54,55,56,57,58,59,60,61

(then I lose my record in game. Have to restart ...)

Records 2
---------

Rule: Play with this [iOS APP](https://itunes.apple.com/ca/app/id574915961). For each model, we plays 2 games, 1 as black, 1 as white. If wins at least once, no matter as black or white, we count it as a 'won'.

Model step-350400 can be downloaded from [here](https://github.com/gooooloo/reversi-alpha-zero-models/tree/master/model_350400-steps)

- step-263200 (100sim): won level ~ 31, lose to level 32
- step-302400 (100sim): won level ~ 44 (level 45 not tested yet)
- step-302400 (40sim): won level ~ 53, lose to level 54 
- step-314400 (40sim): won level ~ 54, lose to level 55
- step-314400 (100sim): won level ~ 58, lose to level 59
- step-314400 (200sim): won level ~ 59, lose to level 60
- step-314400 (400sim): won level ~ 97, lose to level 98
- step-350400 (100sim): won level 98, lose to level 99
- step-350400 (400sim): lose to level 99
- step-350400 (800sim): won level 99

Records 3
---------

Rule: play with NTest. `NTest:xxx` means NTest with strenth xxx. 

For simplicity, a blank cell means losing ALL 10 games, and a '-' means not tested.

Starting from step 411400, I increase computing sources for self-play.
Starting from step 406401, there is a bug of evaluator. I fix it at step 434700.

|           |         |Ntest: 5|Ntest: 6|Ntest: 7|Ntest: 8|Ntest: 9|
|-----------|--------:|:------:|:------:|:------:|:------:|:------:|
|step-350400|  100 sim|  5/0/5 |  1/0/9 |  0/3/7 |        |        |
|step-350400|  200 sim|  5/0/5 |        |        |  0/4/6 |        |
|step-350400|  400 sim|  8/0/2 |  2/0/8 |  1/2/7 |  0/5/5 |        |
|step-350400|  800 sim|  1/4/5 |  5/0/5 |  3/0/7 |  3/2/5 |  0/2/8 |
|step-386400|  100 sim|        |  3/0/7 |  0/1/9 |  4/0/6 |        |
|step-386400|  200 sim|  5/0/5 |  7/0/3 |        |  5/0/5 |        |
|step-386400|  400 sim|  4/0/6 | 10/0/0 |  3/0/7 |  4/0/6 |  2/0/8 |
|step-386400|  800 sim|  2/1/7 |  7/0/3 |  1/2/7 |  5/0/5 |        |
|step-406400|  100 sim|        |  4/0/6 |        |  4/0/6 |        |
|step-406400|  200 sim|        |  2/0/8 |        |  4/0/6 |        |
|step-406400|  400 sim|  4/0/6 |  4/0/6 |        |  5/0/5 |        |
|step-406400|  800 sim|  3/2/5 |  7/0/3 |  0/1/9 |  5/0/5 |        |
|step-406400| 3200 sim|   -    |   -    |   -    |   -    |  8/0/2 |
|step-406400| 6400 sim|   -    |   -    |   -    |   -    |  6/1/3 |
|step-406400|12800 sim|   -    |   -    |   -    |   -    |  5/0/5 |
|step-417700|  100 sim|   -    |   -    |   -    |   -    |        |
|step-417700|  400 sim|   -    |   -    |   -    |   -    |  4/2/4 |
|step-417700|  800 sim|   -    |   -    |   -    |   -    |  0/5/5 |
|step-418500|  100 sim|   -    |   -    |   -    |   -    |  3/0/7 |
|step-418500|  400 sim|   -    |   -    |   -    |   -    |  7/0/3 |
|step-418500|  800 sim|   -    |   -    |   -    |   -    |  5/0/5 |


|           |         |Ntest:10|Ntest:11|Ntest:12|Ntest:13|
|-----------|--------:|:------:|:------:|:------:|:------:|
|step-386400|  100 sim|  1/0/9 |        |        |        |
|step-386400|  200 sim|        |        |        |        |
|step-386400|  400 sim|  0/1/9 |  0/5/5 |        |        |
|step-386400|  800 sim|        |  0/5/5 |        |        |
|step-391200|  100 sim|        |        |  0/1/9 |        |
|step-391200|  200 sim|        |        |        |        |
|step-391200|  400 sim|        |        |        |        |
|step-391200|  800 sim|        |        |  1/0/9 |        |
|step-401600|  100 sim|        |        |        |        |
|step-401600|  200 sim|        |        |        |        |
|step-401600|  400 sim|        |        |  0/1/9 |        |
|step-401600|  800 sim|        |        |        |        |
|step-406400|  100 sim|        |        |        |        |
|step-406400|  200 sim|  0/3/7 |        |        |        |
|step-406400|  400 sim|        |  0/4/6 |        |  0/1/9 |
|step-406400|  800 sim|        |  0/1/9 |  0/2/8 |  0/2/8 |
|step-406400| 3200 sim|  1/2/7 |  4/1/5 |   -    |   -    |
|step-406400| 6400 sim|  1/0/9 |  1/2/7 |   -    |   -    |
|step-406400|12800 sim|  2/1/7 |   -    |   -    |   -    |
|step-411300|  100 sim|        |        |        |        |
|step-411300|  200 sim|        |        |        |        |
|step-411300|  400 sim|        |        |        |        |
|step-411300|  800 sim|        |        |  2/0/8 |        |
|step-417700|  100 sim|        |        |        |        |
|step-417700|  400 sim|  1/0/9 |  1/1/8 |  1/0/9 |        |
|step-417700|  800 sim|  2/0/8 |        |  4/0/6 |        |
|step-418500|  100 sim|        |        |        |        |
|step-418500|  400 sim|        |        |        |        |
|step-418500|  800 sim|  2/0/8 |        |        |        |
|step-432200|  100 sim|        |        |        |        |
|step-432200|  200 sim|        |        |        |        |
|step-432200|  400 sim|        |        |        |  5/0/5 |
|step-432200|  800 sim|  2/0/8 |        |  0/3/7 |  1/1/8 |
|step-437800|    5 min|        |  1/1/8 |  5/0/5 |  0/2/8 |
|step-442600|    5 min|  2/1/7 |        |        |  4/3/3 |


|           |         |Ntest:14|Ntest:15|Ntest:16|
|-----------|--------:|:------:|:------:|:------:|
|step-437800|    5 min|  0/4/6 |        |        |
|step-442600|    5 min|        |        |  0/1/9 |

