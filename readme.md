docker build -t fastapi-app .

kubectl apply -f deployment.yaml

kubectl get deployments
kubectl get pods

kubectl expose deployment fastapi-app --type=LoadBalancer --port=80

kubectl get services
