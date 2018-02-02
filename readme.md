About
=====

Reversi reinforcement learning of [AlphaGo zero](https://deepmind.com/blog/alphago-zero-learning-scratch/) and [Alpha Zero](https://arxiv.org/abs/1712.01815) methods.


Environment
-----------

* Ubuntu / OSX. I don't tested it in Windows.
* Python 3.6
* tensorflow-gpu: 1.3.0+
* Keras: 2.0.8


Download Pretrained Model to Play with
==========

[Here](https://github.com/gooooloo/reversi-alpha-zero-models)


Training Pipeline Examples
==========

Below are some examples for usage. Check the codes for detailed usage information (`src/reversi_zero/manager.py` would be a good entry point).


Self-Play
--------

```bash
python3.6 -m src.reversi_zero.run self --env reversi
```
```bash
python3.6 -m src.reversi_zero.run self --env reversi --n-workers 4 
```
```bash
python3.6 -m src.reversi_zero.run self --env reversi --n-workers 4 --gpu-memory-frac 0.8
```
```bash
python3.6 -m src.reversi_zero.run self --env reversi --n-workers 4 --can-resign False
```

Maintaining resignation threshold
-------

```bash
# Required for self play in my enrivonment. Maybe you don't need it.
python3.6 -m src.reversi_zero.run res --env reversi
```

Trainer
-------

```bash
# AlphaZero style
python3.6 -m src.reversi_zero.run opt --env reversi
```

```bash
# AlphaGoZero style
python3.6 -m src.reversi_zero.run opt --env reversi  --need-eval True
```

Evaluator
---------

```bash
python3.6 -m src.reversi_zero.run eval
```

```bash
python3.6 -m src.reversi_zero.run eval --n-workers 4
```

Play Game Examples
==========

Start Http Server
---------

```bash
# use best model
python3.6 -m src.reversi_zero.run http_server --env reversi
```
```bash
# have a chance to select specific generation of model from console
python3.6 -m src.reversi_zero.run http_server --env reversi --ask-model true
```
```bash
# specify simulations per move
python3.6 -m src.reversi_zero.run http_server --env reversi --n-sims 100
```
```bash
# use the specific generation of model
python3.6 -m src.reversi_zero.run http_server --env reversi --n-steps-model 424000
```
```bash
# set the http port
python3.6 -m src.reversi_zero.run http_server --env reversi --http-port 8888
```


Play GUI
---------

```bash
python3.6 -m src.reversi_zero.run play_gui --env reversi
```
```bash
# show local GUI, but the model run on another server.
pythonw -m src.reversi_zero.run play_gui --env reversi --http-url http://192.168.31.9:8888
```

Play with NTest
---------

[NTest](https://github.com/weltyc/ntest) is a very strong Reversi AI. We can play with it automatically. Just modify `batch.ntest.sh` and run.

```bash
. ./batch.ntest.sh
```

Play between different generations of model
---------

Sometimes I want to compete strength of different models. So I setup the models in `src/reversi_zero/worker/league.py` and run.

```bash
python3.6 -m src.reversi_zero.run league --env reversi --n-workers 4
```


Strength Records
==========

see 'records.sh' in this folder.

Credit
==========

- My codes are based on @mokemokechicken 's [original implementation](https://github.com/mokemokechicken/reversi-alpha-zero), which is really great.
- My multi-process idea is borrowed from @akababa 's [repo](https://github.com/Akababa/Chess-Zero).
