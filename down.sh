# Check if an argument was provided
if [ $# -eq 0 ]; then
  echo "Usage: $0 path_to_python_module"
  exit 1
fi

# Kill all background processes related to the specified Python module
echo "Killing all background processes for the module..."
pkill -f "$server_module_path"

# Assign the first argument to server_module_path
server_module_path="$1"

# Stop the Redis server
echo "Stopping Redis server..."
sudo service redis-server stop

# Stop Nginx
echo "Stopping Nginx..."
sudo systemctl stop nginx



echo "All services and processes have been stopped."