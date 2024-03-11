# Usage:
#   ./up.sh [path_to_server_module] -n [number of instances] -> will begin on port 5701
# e.g., ./up.sh --module examples.cogrid_overcooked.overcooked_human_ai_server -n 3 -b -r

# Initialize default values
num_instances=1
start_port=5701
start_redis=0
start_nginx=0
public_ip=$(curl -s ifconfig.me)
server_module_path=""
nginx_config_template="configurations/interactive-gym-nginx.conf"


# Process command line options
# Process command line options
while getopts ":n:rbl-:" opt; do
  case ${opt} in
    n )
      num_instances=$OPTARG
      ;;
    r )
      start_redis=1
      ;;
    b )
      start_nginx=1
      ;;
    l )
      public_ip="127.0.0.1"
      ;;
    - )
      case "${OPTARG}" in
        module)
          val="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
          server_module_path=$val
          ;;
        *)
          echo "Invalid option: --${OPTARG}" >&2
          exit 1
          ;;
      esac
      ;;
    \? )
      echo "Usage: cmd [-n number_of_instances] [-r] [-b] [-l] [--module path_to_python_module]"
      echo "  -n: Number of Flask instances to start"
      echo "  -r: Start Redis queue service"
      echo "  -b: Start Nginx for load balancing"
      echo "  -l: Run only on localhost (127.0.0.1)"
      echo "  --module: Path to the Python app module."
      exit 1
      ;;
  esac
done
# Debug: Print the options
echo "Number of instances: $num_instances"
echo "Start Redis: $start_redis"
echo "Start Nginx: $start_nginx"
echo "Server Module Path: $server_module_path"

# Start Redis server if requested
if [ "$start_redis" -eq 1 ]; then
    echo "Starting Redis server..."
    sudo service redis-server start
fi

# Prepare and start Nginx with dynamic configuration
if [ "$start_nginx" -eq 1 ]; then
  echo "Preparing Nginx configuration..."
    # Generate upstream block with ip_hash
    upstream_block="upstream flaskapp {\n    ip_hash;\n"
    for ((i=0; i<num_instances; i++)); do
        port=$(($start_port + $i))
        upstream_block+="    server $public_ip:$port;\n"
    done
    upstream_block+="}\n"

    # Create a new temporary nginx configuration file
    temp_nginx_conf=$(mktemp)

    # Process the original Nginx configuration template
    # To replace the existing upstream block and preserve the rest of the configuration
    awk -v replacement="$upstream_block" '
      $0 ~ /^upstream flaskapp \{/ { inside = 1; print replacement; next }
      $0 ~ /^\}/ && inside { inside = 0; next }
      !inside { print }
    ' $nginx_config_template > "$temp_nginx_conf"

    # Instead of overwriting the nginx_config_template, move the modified configuration directly to /etc/nginx/conf.d/
    echo "Copying Nginx configuration to /etc/nginx/conf.d/"
    cat $temp_nginx_conf
    sudo mv "$temp_nginx_conf" "/etc/nginx/conf.d/$(basename $nginx_config_template)"


  # Start or reload Nginx
  echo "Starting Nginx for load balancing..."
  sudo systemctl restart nginx || sudo systemctl start nginx
  sudo systemctl enable nginx
  sudo nginx -t && sudo systemctl reload nginx
fi


# Start the Flask app instances
for ((i=0; i<num_instances; i++)); do
  port=$(($start_port + $i))
  echo "Starting instance on port $port..."
  nohup python -m $server_module_path --port $port > log_$port.txt 2>&1 &
done

echo "Started $num_instances instances on host $public_ip, ports $start_port - $(($start_port + $num_instances - 1))."