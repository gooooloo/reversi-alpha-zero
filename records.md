Strength Records
==========

Challenge 1 
---------

Challenge 1 is using the AlphaGoZero way,  which has a 'Evaluator' module. Not AlphaZero way.

It ends at step 545800. When it ends, the last git commit is 37392e3207d7c36ffdb502a543bb24847825e928.
It starts at 2017-12-23, ends at 2018-02-11, so it takes about 50 days.
I didn't record how many self-play data it generates.

Finally I would say its strength is near a position of NTest depth 10+.

Evaluator is getting half games ends up with draw. I feel there is no more obvious progress. So I end it up.


Challenge 1 - Records 1
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

Challenge 1 - Records 2
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

Challenge 1 - Records 3
---------

Rule: play with NTest. `NTest:xxx` means NTest with strenth xxx. `x/y/z` means x wins, y draws, z loses.

For simplicity, a blank cell means losing ALL 10 games (for 30 min, it is 4 games by default), and a '-' means not tested.
Some of winning/draw game savings can be downloaded from [here](http://github.com/gooooloo/reversi-alpha-zero-models/tree/master/ggf)

Why use 30 min? Actually I am targeting 5 min C++ implementation on a 8-core CPU, 1-GPU machine. But I don't have a C++ implementation yet, so I try a python with 30 min. I believe they will be similar in simulation_number_per_move, which is about 13000.

- Starting from step 411400, I increase computing sources for self-play. As a result, the selfplay speed raises from about 500 games per hour to about 1150 games per hour (with 800 simlulations per move). Opt speed keeps not changed, 12 minutes training 100 steps.
- Starting from step 406401, there is a bug of evaluator. I fix it at step 434700.
- Starting from step 531100, I use model-cache.

|           |         |  Ntest: 5 |  Ntest: 5 |  Ntest: 6 |  Ntest: 6 |  Ntest: 7 |  Ntest: 7 |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|
|step-350400|  100 sim|           |W **5/0/0**|  B 1/0/4  |           |           |  W 0/3/2  |
|step-350400|  200 sim|           |W **5/0/0**|           |           |           |           |
|step-350400|  400 sim|B **3/0/2**|W **5/0/0**|  B 1/0/4  |  W 1/0/4  |  B 1/2/2  |           |
|step-350400|  800 sim|           |W **1/4/0**|  B 2/0/3  |W **3/0/2**|  B 2/0/3  |  W 1/0/4  |
|step-386400|  100 sim|           |           |B **3/0/2**|           |           |  W 0/1/4  |
|step-386400|  200 sim|B **5/0/0**|           |  B 2/0/3  |W **5/0/0**|           |           |
|step-386400|  400 sim|B **4/0/1**|           |B **5/0/0**|W **5/0/0**|B **3/0/2**|           |
|step-386400|  800 sim|B **2/1/2**|           |B **5/0/0**|  W 2/0/3  |  B 1/0/4  |  W 0/2/3  |
|step-406400|  100 sim|           |           |  B 2/0/3  |  W 2/0/3  |           |           |
|step-406400|  200 sim|           |           |  B 2/0/3  |           |           |           |
|step-406400|  400 sim|B **4/0/1**|           |B **4/0/1**|           |           |           |
|step-406400|  800 sim|B **3/2/0**|           |B **3/0/2**|W **4/0/1**|  B 0/1/4  |           |
|step-418500|  400 sim|  B 1/0/4  |  W 0/2/3  |B **2/1/2**|W **4/0/1**|           |  W 0/4/1  |
|step-418500|  800 sim|B **3/2/0**|  W 0/3/2  |           |W **5/0/0**|           |W **4/0/1**|
|step-432200|  400 sim|  B 1/1/3  |           |B **4/0/1**|           |           |W **4/0/1**|
|step-432200|  800 sim|B **4/0/1**|  W 0/2/3  |B **4/0/1**|  W 1/0/4  |B **3/0/2**|           |
|step-442600|  400 sim|  B 2/0/3  |W **5/0/0**|           |           |           |           |
|step-442600|  800 sim|B **5/0/0**|W **5/0/0**|B **3/0/2**|           |  B 1/0/4  |           |
|step-453800|  400 sim|B **5/0/0**|W **0/5/0**|           |           |           |           |
|step-453800|  800 sim|B **5/0/0**|W **1/4/0**|           |           |B **4/0/1**|           |
|step-471400|  400 sim|B **3/0/2**|           |  B 1/0/4  |W **3/0/2**|  B 0/1/4  |W **0/5/0**|
|step-471400|  800 sim|B **4/0/1**|           |  B 2/0/3  |W **5/0/0**|           |  W 0/4/1  |
|step-473800|   30 min|     -     |     -     |     -     |     -     |B **1/1/0**|W **1/0/1**|
|step-473800|  400 sim|  B 1/0/4  |W **4/0/1**|           |  W 2/0/3  |           |  W 0/2/3  |
|step-473800|  800 sim|B **5/0/0**|  W 2/0/3  |B **3/0/2**|W **5/0/0**|B **4/0/1**|           |
|step-482600|  800 sim|B **3/2/0**|W **5/0/0**|  B 1/0/4  |W **5/0/0**|B **5/0/0**|           |
|step-485800|   30 min|B **2/0/0**|W **2/0/0**|B **2/0/0**|W **2/0/0**|B **2/0/0**|W **2/0/0**|
|step-497000|  800 sim|     -     |     -     |     -     |     -     |B **3/0/2**|           |

|           |         |  Ntest: 8 |  Ntest: 8 |  Ntest: 9 |  Ntest: 9 |  Ntest:10 |  Ntest:10 |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|
|step-350400|  100 sim|           |           |           |           |     -     |     -     |
|step-350400|  200 sim|  B 0/4/1  |           |           |           |     -     |     -     |
|step-350400|  400 sim|B **0/5/0**|           |           |           |     -     |     -     |
|step-350400|  800 sim|B **3/2/0**|           |           |  W 0/2/3  |     -     |     -     |
|step-386400|  100 sim|B **4/0/1**|           |           |           |  B 1/0/4  |           |
|step-386400|  200 sim|B **5/0/0**|           |           |           |           |           |
|step-386400|  400 sim|  B 1/0/4  |W **3/0/2**|  B 2/0/3  |           |           |  W 0/1/4  |
|step-386400|  800 sim|  B 1/0/4  |W **4/0/1**|           |           |           |           |
|step-391200|  800 sim|     -     |     -     |     -     |     -     |           |           |
|step-401600|  800 sim|     -     |     -     |     -     |     -     |           |           |
|step-406400|  100 sim|B **4/0/1**|           |           |           |           |           |
|step-406400|12800 sim|     -     |     -     |           |W **5/0/0**|B **2/1/2**|           |
|step-406400|  200 sim|B **4/0/1**|           |           |           |  B 0/3/2  |           |
|step-406400| 3200 sim|     -     |     -     |B **3/0/2**|W **5/0/0**|  B 1/2/2  |           |
|step-406400|  400 sim|B **5/0/0**|           |           |           |           |           |
|step-406400| 6400 sim|     -     |     -     |  B 1/1/3  |W **5/0/0**|  B 1/0/4  |           |
|step-406400|  800 sim|B **5/0/0**|           |           |           |           |           |
|step-411300|  800 sim|     -     |     -     |     -     |     -     |           |           |
|step-417700|  100 sim|     -     |     -     |           |           |           |           |
|step-417700|  400 sim|     -     |     -     |  B 1/0/4  |W **3/2/0**|  B 1/0/4  |           |
|step-417700|  800 sim|     -     |     -     |           |W **0/5/0**|  B 2/0/3  |           |
|step-418500|  100 sim|     -     |     -     |B **3/0/2**|           |           |           |
|step-418500|  400 sim|  B 0/3/2  |           |B **5/0/0**|  W 2/0/3  |           |           |
|step-418500|  800 sim|B **2/3/0**|  W 1/0/4  |B **4/0/1**|  W 1/0/4  |  B 2/0/3  |           |
|step-432200|  400 sim|B **2/1/2**|           |B **3/0/2**|           |           |           |
|step-432200|  800 sim|  B 1/0/4  |           |  B 1/0/4  |           |  B 2/0/3  |           |
|step-437800|    5 min|     -     |     -     |     -     |     -     |           |           |
|step-442600|  400 sim|           |           |  B 1/0/4  |           |     -     |     -     |
|step-442600|    5 min|     -     |     -     |     -     |     -     |  B 2/0/3  |  W 0/1/4  |
|step-442600|  800 sim|  B 2/0/3  |W **4/0/1**|B **3/0/2**|           |     -     |     -     |
|step-445800|    5 min|     -     |     -     |     -     |     -     |           |           |
|step-451400|  800 sim|     -     |     -     |     -     |     -     |           |           |
|step-453800|  400 sim|  B 2/0/3  |           |           |           |           |           |
|step-453800|  800 sim|           |  W 2/0/3  |  B 1/0/4  |           |           |           |
|step-471400|  400 sim|           |           |           |           |           |           |
|step-471400|  800 sim|           |W **4/0/1**|           |  W 0/4/1  |           |  W 0/2/3  |
|step-473800|   30 min|B **2/0/0**|W **2/0/0**|B **2/0/0**|W **2/0/0**|B **2/0/0**|W **2/0/0**|
|step-473800|  400 sim|           |W **4/0/1**|           |  W 1/0/4  |           |           |
|step-473800|    5 min|     -     |     -     |     -     |     -     |B **1/0/1**|W **0/2/0**|
|step-473800|  800 sim|           |W **4/0/1**|           |           |  B 1/0/4  |           |
|step-482600|  800 sim|  B 0/1/4  |           |B **2/2/1**|           |  B 0/3/2  |W **0/5/0**|
|step-485800|   30 min|B **2/0/0**|W **2/0/0**|B **1/0/1**|W **2/0/0**|           |W **2/0/0**|
|step-497000|  800 sim|           |W **5/0/0**|B **4/0/1**|           |  B 1/0/4  |           |
|step-513800|  800 sim|     -     |     -     |     -     |     -     |           |  W 1/0/4  |


|           |         |  Ntest:11 |  Ntest:11 |  Ntest:12 |  Ntest:12 |  Ntest:13 |  Ntest:13 |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|
|step-386400|  400 sim|           |W **0/5/0**|           |           |           |           |
|step-386400|  800 sim|           |W **0/5/0**|           |           |           |           |
|step-391200|  100 sim|           |           |  B 0/1/4  |           |           |           |
|step-391200|  400 sim|           |           |           |           |           |           |
|step-391200|  800 sim|           |           |           |  W 1/0/4  |           |           |
|step-401600|  400 sim|           |           |           |  W 0/1/4  |           |           |
|step-401600|  800 sim|           |           |           |           |           |           |
|step-406400| 3200 sim|  B 1/0/4  |W **3/1/1**|     -     |     -     |     -     |     -     |
|step-406400|  400 sim|           |  W 0/4/1  |           |           |           |  W 0/1/4  |
|step-406400| 6400 sim|           |  W 1/2/2  |     -     |     -     |     -     |     -     |
|step-406400|  800 sim|           |  W 0/1/4  |           |  W 0/2/3  |           |  W 0/2/3  |
|step-411300|  400 sim|           |           |           |           |           |           |
|step-411300|  800 sim|           |           |  B 2/0/3  |           |           |           |
|step-417700|  400 sim|  B 1/1/3  |           |           |  W 1/0/4  |           |           |
|step-417700|  800 sim|           |           |           |W **4/0/1**|           |           |
|step-418500|  400 sim|           |           |           |           |           |           |
|step-418500|  800 sim|           |           |           |           |           |           |
|step-432200|  400 sim|           |           |           |           |B **5/0/0**|           |
|step-432200|  800 sim|           |           |           |  W 0/3/2  |  B 1/1/3  |           |
|step-437800|    5 min|  B 0/1/4  |  W 1/0/4  |           |W **5/0/0**|           |  W 0/2/3  |
|step-442600|    5 min|           |           |           |           |B **4/0/1**|  W 0/3/2  |
|step-445800|    1 min|           |           |           |           |           |           |
|step-445800|    5 min|           |           |           |  W 1/2/2  |  B 1/0/4  |           |
|step-451400|   30 min|     -     |     -     |     -     |     -     |  B 0/1/1  |           |
|step-451400|  400 sim|           |           |           |           |           |           |
|step-451400|  800 sim|  B 1/0/4  |           |           |           |           |           |
|step-453800|   30 min|     -     |     -     |     -     |     -     |           |           |
|step-453800|  400 sim|           |           |           |           |           |           |
|step-453800|  800 sim|  B 0/1/4  |           |           |           |           |           |
|step-471400|  400 sim|  B 1/0/4  |           |           |           |           |           |
|step-471400|  800 sim|           |           |           |           |           |  W 0/2/3  |
|step-473800|   30 min|B **2/0/0**|           |B **0/2/0**|W **2/0/0**|B **1/1/0**|W **2/0/0**|
|step-473800|  400 sim|           |           |           |           |           |           |
|step-473800|  800 sim|           |           |           |  W 2/0/3  |           |W **3/0/2**|
|step-482600|  800 sim|B **0/5/0**|           |           |           |           |           |
|step-485800|   30 min|           |W **1/0/1**|B **1/0/1**|W **1/1/0**|           |W **1/1/0**|
|step-497000|  800 sim|  B 2/0/3  |W **0/5/0**|  B 1/0/4  |           |           |           |
|step-513800|  800 sim|           |           |  B 1/0/4  |W **5/0/0**|  B 0/1/4  |           |
|step-533800|   30 min|           |W **0/2/0**|           |W **0/2/0**|           |W **0/2/0**|
|step-533800|  800 sim|           |           |           |           |           |           |
|step-534600|   30 min|B **1/0/1**|  W 0/1/1  |           |W **2/0/0**|           |W **1/1/0**|
|step-534600|  800 sim|           |  W 1/0/4  |           |           |           |           |
|step-541800|  800 sim|           |W **5/0/0**|           |           |           |           |
|step-545800|  800 sim|B **4/0/1**|  W 0/4/1  |           |           |           |           |

|           |         |  Ntest:14 |  Ntest:14 |  Ntest:15 |  Ntest:15 |  Ntest:16 |  Ntest:16 |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|
|step-437800|    5 min|           |  W 0/4/1  |           |           |           |           |
|step-442600|    5 min|           |           |           |           |  B 0/1/4  |           |
|step-445800|    1 min|           |           |     -     |     -     |     -     |     -     |
|step-445800|   30 min|  B 0/1/1  |W **2/0/0**|           |W **1/0/1**|           |  W 0/1/1  |
|step-451400|   30 min|B **1/0/1**|           |           |W **0/2/0**|           |           |
|step-451400|  400 sim|           |           |           |           |           |           |
|step-451400|  800 sim|           |           |           |           |           |           |
|step-453800|   30 min|           |           |           |           |           |           |
|step-453800|  400 sim|           |           |           |           |           |           |
|step-453800|  800 sim|           |           |           |           |           |           |
|step-473800|   30 min|B **0/2/0**|           |  B 0/1/1  |           |           |W **0/2/0**|
|step-473800|  800 sim|  B 0/1/4  |           |           |           |  B 0/2/3  |           |
|step-485800|   30 min|           |  W 0/1/1  |           |           |B **1/0/1**|           |
|step-513800|   30 min|           |           |           |  W 0/1/1  |           |W **1/0/1**|
|step-513800|  800 sim|           |           |           |           |           |           |
|step-513800|   90 min|     -     |     -     |           |  W 0/1/1  |     -     |     -     |
|step-533800|   30 min|B **1/0/1**|  W 0/1/1  |B **2/0/0**|           |           |W **2/0/0**|
|step-533800|  800 sim|  B 0/2/3  |W **0/5/0**|           |           |           |W **5/0/0**|
|step-534600|   30 min|           |W **1/0/1**|           |  W 0/1/1  |           |           |
|step-534600|  800 sim|  B 0/2/3  |           |     -     |     -     |     -     |     -     |


|           |         |  Ntest:17 |  Ntest:17 |  Ntest:18 |  Ntest:18 |  Ntest:19 |  Ntest:19 |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|
|step-533800|   30 min|           |  W 0/1/1  |           |W **2/0/0**|           |W **0/2/0**|
|step-534600|   30 min|           |W **0/2/0**|           |W **2/0/0**|           |           |


|           |         |  Ntest:20 |  Ntest:20 |
|-----------|--------:|:---------:|:---------:|
|step-533800|   30 min|           |           |
|step-534600|   30 min|           |  W 0/1/1  |


Challenge 2
---------

Using the AlphaZero way -- no Evaluator. The corresponding codes are [commit 60e109d](https://github.com/gooooloo/reversi-alpha-zero/commit/60e109d30cadf0318a1837e7a5b865d707b69b7b).

- From step 45400, change model update/reloading frequentcy. [commit a960406](https://github.com/gooooloo/reversi-alpha-zero/commit/a9604062f0f53a42492a96453378aa6e0e8f4d81)
- From step 48000, change model fix the model synchronization issue. [commit 73bb578](https://github.com/gooooloo/reversi-alpha-zero/commit/73bb578bd307e2bb68728561d0720b0a9cc5acf8)
- I observe loss doesn't change from about step 30000+. At about step 50000, I give up. Maybe it is because self play's model changes too frequently, so 1 game is using about 5 models?


Challenge 2 - Opt/Self-Play Speed Ratio
---------

Some data collected at the moment of training step 9400:

- Train: 9400 * 3072 = 28,876,800 moves
- Self-Play: 1928907 * 8 = 15,431,256 moves (after symmetric augmented)
- So every move is trained 28,876,800 / 15,431,256 = 1.87 times.
- Time since start: ~20 hours, so ~1,440,000 training steps per hour, ~770,000 self play moves per hour (after symmetric augmented).



Challenge 2 - AI Strength Record
---------

|           |         |  Ntest: 1 |  Ntest: 1 |  Ntest: 2 |  Ntest: 2 |  Ntest: 3 |  Ntest: 3 |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|
|step-     0|  800 sim|  B 1/0/4  |           |           |           |           |           |
|step-  6400|  800 sim|           |W **5/0/0**|           |           |           |           |
|step- 12800|  800 sim|           |           |           |           |           |           |
|step- 19200|  800 sim|           |           |           |           |           |           |
|step- 25600|  800 sim|B **4/0/1**|           |           |           |  B 1/0/4  |           |
|step- 32000|  800 sim|  B 1/0/4  |           |           |           |           |           |
|step- 38400|  800 sim|           |           |           |           |           |           |
|step- 44800|  800 sim|           |           |           |           |           |           |


Challenge 3
---------

Using the AlphaZero way -- no Evaluator. The corresponding codes are [commit 60e109d](https://github.com/gooooloo/reversi-alpha-zero/commit/60e109d30cadf0318a1837e7a5b865d707b69b7b).

- Compared with Challenge 2, change is I reload model every 400 seconds, longer than a typically game length (300+ seconds).
- Moves number in training pool is about 2,400,000 * 8 moves to 2,750,000 * 8 moves. (So according to 'Total Moves' changing speed as below, it is roughly about 10,000 training step).
- From about step 8000, codes are [commit 41ee8ee](https://github.com/gooooloo/reversi-alpha-zero/commit/41ee8eeddccf2f0ccc327740978a4aab3766ec59)
- From step 38690, codes are [commit 9829645](https://github.com/gooooloo/reversi-alpha-zero/commit/9829645ef29e678b6c770cd429c67b3f72537ecb). It fixes a probility bug in MCTS.
- From step 77600, codes are [commit 95e27a0](https://github.com/gooooloo/reversi-alpha-zero/commit/95e27a0164e731bae5fbc9210e487f6a38805e6c). It changes learning rate from 0.002 to 0.0002.
- From step 112030, self play cannot resign.

Challenge 3 - AI Strength Record
---------

|           |         |  Ntest: 1 |  Ntest: 1 |  Ntest: 2 |  Ntest: 2 |  Ntest: 3 |  Ntest: 3 |Policy Loss| Value Loss|Total Moves |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:----------:|
|step-     0|  800 sim|  B 1/0/4  |  W 1/0/4  |           |           |           |           |     -     |     -     |      0     |
|step-  6400|  800 sim|           |W **5/0/0**|           |           |           |           |     -     |     -     | 1282180 * 8|
|step- 12800|  800 sim|           |           |           |           |           |           |  1.3831   |   0.5729  | 2551232 * 8|
|step- 19200|  800 sim|           |           |           |           |           |           |  1.1385   |   0.5662  | 4134764 * 8|
|step- 25600|  800 sim|B **4/0/1**|           |           |           |           |           |  0.9961   |   0.5541  | 5642099 * 8|
|step- 32000|  800 sim|  B 2/0/3  |           |           |           |           |           |  0.9586   |   0.5556  | 6854500 * 8|
|step- 38400|  800 sim|           |           |           |           |           |           |  0.8732   |   0.5342  | 8407176 * 8|
|step- 44800|  800 sim|           |           |           |           |           |           |  0.6411   |   0.4669  |10522975 * 8|
|step- 51200|  800 sim|B **5/0/0**|W **5/0/0**|B **5/0/0**|W **5/0/0**|B **3/2/0**|W **5/0/0**|  0.5586   |   0.4675  |12066949 * 8|
|step- 57600|  800 sim|B **5/0/0**|W **5/0/0**|B **5/0/0**|W **5/0/0**|B **5/0/0**|W **5/0/0**|  0.5415   |   0.4568  |13434479 * 8|


|           |         |  Ntest: 4 |  Ntest: 4 |  Ntest: 5 |  Ntest: 5 |  Ntest: 6 |  Ntest: 6 |Policy Loss| Value Loss|Total Moves |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:----------:|
|step- 51200|  800 sim|B **5/0/0**|W **4/0/1**|B **4/1/0**|W **5/0/0**|B **4/0/1**|W **5/0/0**|  0.5586   |   0.4675  |12066949 * 8|
|step- 57600|  800 sim|B **4/1/0**|W **5/0/0**|B **3/0/2**|W **5/0/0**|B **5/0/0**|W **5/0/0**|  0.5415   |   0.4568  |13434479 * 8|
|step- 64000|  800 sim|B **5/0/0**|W **5/0/0**|B **5/0/0**|W **5/0/0**|B **4/0/1**|W **5/0/0**|  0.5408   |   0.4546  |14791508 * 8| 
|step- 70400|  800 sim|B **5/0/0**|W **5/0/0**|B **5/0/0**|W **5/0/0**|           |W **0/5/0**|  0.5384   |   0.4519  |16526950 * 8|
|step- 76800|  800 sim|  B 1/0/4  |W **5/0/0**|  B 1/1/3  |W **5/0/0**|B **4/0/1**|W **5/0/0**|  0.5301   |   0.4298  |18334122 * 8|
|step- 84010|  800 sim|B **4/1/0**|W **5/0/0**|B **4/1/0**|W **5/0/0**|B **5/0/0**|W **5/0/0**|  0.4834   |   0.3847  |20840365 * 8|


|           |         |  Ntest: 7 |  Ntest: 7 |  Ntest: 8 |  Ntest: 8 |  Ntest: 9 |  Ntest: 9 |Policy Loss| Value Loss|Total Moves |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:----------:|
|step- 51200|  800 sim|  B 1/0/4  |W **5/0/0**|B **0/5/0**|W **4/0/1**|B **0/5/0**|W **0/5/0**|  0.5586   |   0.4675  |12066949 * 8|
|step- 57600|  800 sim|           |W **5/0/0**|  B 0/1/4  |  W 1/1/3  |B **5/0/0**|W **5/0/0**|  0.5415   |   0.4568  |13434479 * 8|
|step- 64000|  800 sim|  B 1/0/4  |W **5/0/0**|B **5/0/0**|W **5/0/0**|  B 2/0/3  |W **0/5/0**|  0.5408   |   0.4546  |14791508 * 8| 
|step- 70400|  800 sim|B **5/0/0**|W **5/0/0**|           |W **3/0/2**|           |W **3/2/0**|  0.5384   |   0.4519  |16526950 * 8|
|step- 76800|  800 sim|B **3/0/2**|           |B **3/0/2**|W **5/0/0**|           |W **5/0/0**|  0.5301   |   0.4298  |18334122 * 8|
|step- 77610|  800 sim|  B 2/0/3  |W **5/0/0**|B **2/2/1**|W **5/0/0**|B **4/0/1**|W **5/0/0**|     -     |      -    |      -     |
|step- 84010|  800 sim|  B 1/0/4  |W **5/0/0**|  B 2/0/3  |W **5/0/0**|  B 1/2/2  |W **3/2/0**|  0.4834   |   0.3847  |20840365 * 8|
|step- 90410|  800 sim|B **5/0/0**|W **5/0/0**|  B 1/0/4  |W **5/0/0**|           |W **0/5/0**|  0.4071   |   0.3160  |23432337 * 8|
|step- 97170|  800 sim|B **2/3/0**|W **5/0/0**|  B 1/0/4  |W **5/0/0**|  B 2/0/3  |  W 0/2/3  |  0.3431   |   0.2520  |25281461 * 8|
|step-103570|  800 sim|B **1/4/0**|W **5/0/0**|B **4/0/1**|W **5/0/0**|  B 2/0/3  |  W 1/2/2  |  0.3376   |   0.2409  |27247608 * 8|
|step-109970|  800 sim|B **4/1/0**|W **5/0/0**|B **4/0/1**|W **4/0/1**|  B 1/2/2  |W **3/2/0**|     -     |      -    |29260802 * 8|


|           |         | Ntest: 10 | Ntest: 10 | Ntest: 11 | Ntest: 11 | Ntest: 12 | Ntest: 12 |Policy Loss| Value Loss|Total Moves |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:----------:|
|step- 51200|  800 sim|           |           |           |W **0/5/0**|           |           |  0.5586   |   0.4675  |12066949 * 8|
|step- 57600|  800 sim|           |  W 0/1/4  |           |W **0/5/0**|           |  W 0/2/3  |  0.5415   |   0.4568  |13434479 * 8|
|step- 64000|  800 sim|  B 2/0/3  |W **5/0/0**|B **4/0/1**|           |B **3/1/1**|           |  0.5408   |   0.4546  |14791508 * 8|
|step- 70400|  800 sim|B **5/0/0**|           |           |           |           |           |  0.5384   |   0.4519  |16526950 * 8|
|step- 76800|  800 sim|  B 1/0/4  |           |           |           |  B 0/1/4  |           |  0.5301   |   0.4298  |18334122 * 8|
|step- 77610|  800 sim|B **4/0/1**|           |           |           |           |           |     -     |      -    |      -     |
|step- 84010|  800 sim|  B 2/0/3  |           |           |           |  B 2/0/3  |           |  0.4834   |   0.3847  |20840365 * 8|
|step- 90410|  800 sim|  B 1/0/4  |           |           |           |  B 0/4/1  |           |  0.4071   |   0.3160  |23432337 * 8|
|step- 97170|  800 sim|  B 2/0/3  |  W 0/1/4  |           |W **0/5/0**|           |           |  0.3431   |   0.2520  |25281461 * 8|
|step-103570|  800 sim|B **4/0/1**|           |           |  W 0/2/3  |  B 1/1/3  |           |  0.3376   |   0.2409  |27247608 * 8|
|step-109970|  800 sim|B **3/0/2**|  W 0/3/2  |           |           |B **2/1/2**|           |     -     |      -    |29260802 * 8|


|           |         | Ntest: 13 | Ntest: 13 | Ntest: 14 | Ntest: 14 | Ntest: 15 | Ntest: 15 |Policy Loss| Value Loss|Total Moves |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:----------:|
|step- 64000|  800 sim|           |  W 0/4/1  |           |           |           |           |  0.5408   |   0.4546  |14791508 * 8| 
|step- 70400|  800 sim|           |           |B **4/0/1**|           |           |           |  0.5384   |   0.4519  |16526950 * 8|
|step- 76800|  800 sim|           |           |           |           |           |  W 0/1/4  |  0.5301   |   0.4298  |18334122 * 8|
|step- 77610|  800 sim|           |           |  B 0/2/3  |           |           |           |     -     |      -    |      -     |
|step- 84010|  800 sim|  B 0/1/4  |  W 0/3/2  |           |           |  B 0/3/2  |           |  0.4834   |   0.3847  |20840365 * 8|
|step- 90410|  800 sim|           |           |           |           |  B 0/4/1  |           |  0.4071   |   0.3160  |23432337 * 8|
|step- 97170|  800 sim|           |           |           |           |  B 0/4/1  |           |  0.3431   |   0.2520  |25281461 * 8|
|step-103570|  800 sim|  B 0/2/3  |           |           |           |  B 0/2/3  |           |  0.3376   |   0.2409  |27247608 * 8|
|step-109970|  800 sim|  B 1/1/3  |           |           |           |           |  W 0/1/4  |     -     |      -    |29260802 * 8|


I also evaluated with 30 minutes per game.

|           |         |           |           |           |           |           |           |Policy Loss| Value Loss|Total Moves |
|-----------|--------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:---------:|:----------:|
|           |         |  Ntest: 7 |  Ntest: 7 |  Ntest: 8 |  Ntest: 8 |  Ntest: 9 |  Ntest: 9 |           |           |            |
|step- 90410|   30 min|     -     |     -     |     -     |     -     |B **1/0/1**|W **2/0/0**|  0.4071   |   0.3160  |23432337 * 8|
|           |         | Ntest: 10 | Ntest: 10 | Ntest: 11 | Ntest: 11 | Ntest: 12 | Ntest: 12 |           |           |            |
|step- 90410|   30 min|           |W **2/0/0**|     -     |W **0/2/0**|     -     |W **2/0/0**|  0.4071   |   0.3160  |23432337 * 8|
|           |         | Ntest: 13 | Ntest: 13 | Ntest: 14 | Ntest: 14 | Ntest: 15 | Ntest: 15 |           |           |            |
|step- 90410|   30 min|     -     |W **1/0/1**|     -     |           |     -     |W **2/0/0**|  0.4071   |   0.3160  |23432337 * 8|
|           |         | Ntest: 16 | Ntest: 16 | Ntest: 17 | Ntest: 17 | Ntest: 18 | Ntest: 18 |           |           |            |
|step- 90410|   30 min|     -     |           |     -     |W **1/1/0**|     -     |W **2/0/0**|  0.4071   |   0.3160  |23432337 * 8|
|           |         | Ntest: 19 | Ntest: 19 | Ntest: 20 | Ntest: 20 | Ntest: 21 | Ntest: 21 |           |           |            |
|step- 90410|   30 min|     -     |W **2/0/0**|     -     |W **0/2/0**|     -     |W **0/2/0**|  0.4071   |   0.3160  |23432337 * 8|
|           |         | Ntest: 19 | Ntest: 19 | Ntest: 20 | Ntest: 20 | Ntest: 21 | Ntest: 21 |           |           |            |
|step- 90410|   30 min|     -     |W **2/0/0**|     -     |W **0/2/0**|     -     |W **0/2/0**|  0.4071   |   0.3160  |23432337 * 8|
|           |         | Ntest: 22 | Ntest: 22 | Ntest: 23 | Ntest: 23 | Ntest: 24 | Ntest: 24 |           |           |            |
|step- 90410|   30 min|     -     |           |     -     |           |     -     |W **0/2/0**|  0.4071   |   0.3160  |23432337 * 8|
|step-103570|   30 min|     -     |  W 0/1/1  |     -     |W **1/0/1**|     -     |W **0/2/0**|  0.3376   |   0.2409  |27247608 * 8|
|step-109970|   30 min|           |           |           |  W 0/1/1  |           |  W 0/1/1  |     -     |      -    |29260802 * 8|
|           |         | Ntest: 25 | Ntest: 25 | Ntest: 26 | Ntest: 26 | Ntest: 27 | Ntest: 27 |           |           |            |
|step-103570|   30 min|     -     |  W 0/1/1  |     -     |     -     |     -     |     -     |  0.3376   |   0.2409  |27247608 * 8|
|step-109970|   30 min|           |W **2/0/0**|           |           |           |W **2/0/0**|     -     |      -    |29260802 * 8|
|           |         | Ntest: 28 | Ntest: 28 | Ntest: 29 | Ntest: 29 | Ntest: 30 | Ntest: 30 |           |           |            |
|step-109970|   30 min|           |           |           |           |           |W **2/0/0**|     -     |      -    |29260802 * 8|
|           |         | Ntest: 31 | Ntest: 31 | Ntest: 32 | Ntest: 32 | Ntest: 33 | Ntest: 33 |           |           |            |
|step-109970|   30 min|  B 0/1/1  |W **2/0/0**|     -     |     -     |     --    |     -     |     -     |      -    |29260802 * 8|
