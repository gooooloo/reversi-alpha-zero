log=/tmp/batch.ntest.sh.result.log
echo '' > $log
for ndepth in `echo 10 11 12 13`; do
	for nsteps in `echo 386400 391200 401600 406400`; do
		for nsims in `echo 100 200 400 800`; do
			cmd=`echo python -m src.reversi_zero.run elo_p1_ntest --env reversi --n-workers 4 --n-games 10 --ntest-depth $ndepth --n-sims $nsims --n-steps-model $nsteps --save-versus-dir ./data/reversi/ggf/`
			echo $cmd
			echo $cmd >> $log
			eval $cmd >> $log
		done
	done
done

echo check out $log for result!
