echo "=== install ==="

pip install .

echo "=== start ==="


mkdir  ./logs

python examples/remote_agent1.py >./logs/agent1.log 2>&1 &
python examples/remote_agent2.py >./logs/agent2.log 2>&1 &
python examples/remote_team.py >./logs/team.log 2>&1 &


echo "=== test ==="

sleep 10
python examples/test_a2a_server.py
python examples/test_a2a_agents.py


