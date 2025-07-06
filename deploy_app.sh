#!/bin/bash

# This script deploys all Kubernetes resources for the multi-service application.
# It should be run from the root directory.

echo -e "\n--- Deploying Kubernetes Resources ---"

echo -e "\n1. Applying namespace.yaml..."
kubectl apply -f ./multi-service-app/namespace.yaml
if [ $? -ne 0 ]; then echo "Error applying namespace.yaml. Exiting."; exit 1; fi

echo -e "\n2. Applying database resources..."
kubectl apply -f ./multi-service-app/database/persistentVolume.yaml
if [ $? -ne 0 ]; then echo "Error applying database/persistentVolume.yaml. Exiting."; exit 1; fi
kubectl apply -f ./multi-service-app/database/persistentVolumeClaim.yaml
if [ $? -ne 0 ]; then echo "Error applying database/persistentVolumeClaim.yaml. Exiting."; exit 1; fi
kubectl apply -f ./multi-service-app/database/deployment.yaml
if [ $? -ne 0 ]; then echo "Error applying database/deployment.yaml. Exiting."; exit 1; fi
kubectl apply -f ./multi-service-app/database/service.yaml
if [ $? -ne 0 ]; then echo "Error applying database/service.yaml. Exiting."; exit 1; fi

echo -e "\n3. Applying stocks service resources..."
kubectl apply -f ./multi-service-app/stocks/deployment.yaml
if [ $? -ne 0 ]; then echo "Error applying stocks/deployment.yaml. Exiting."; exit 1; fi
kubectl apply -f ./multi-service-app/stocks/service.yaml
if [ $? -ne 0 ]; then echo "Error applying stocks/service.yaml. Exiting."; exit 1; fi

echo -e "\n4. Applying capital-gains service resources..."
kubectl apply -f ./multi-service-app/capital-gains/deployment.yaml
if [ $? -ne 0 ]; then echo "Error applying capital-gains/deployment.yaml. Exiting."; exit 1; fi
kubectl apply -f ./multi-service-app/capital-gains/service.yaml
if [ $? -ne 0 ]; then echo "Error applying capital-gains/service.yaml. Exiting."; exit 1; fi

echo -e "\n5. Applying NGINX service resources..."
kubectl apply -f ./multi-service-app/nginx/configmap.yaml
if [ $? -ne 0 ]; then "Error applying nginx/configmap.yaml. Exiting."; exit 1; fi
kubectl apply -f ./multi-service-app/nginx/deployment.yaml
if [ $? -ne 0 ]; then "Error applying nginx/deployment.yaml. Exiting."; exit 1; fi
kubectl apply -f ./multi-service-app/nginx/service.yaml
if [ $? -ne 0 ]; then "Error applying nginx/service.yaml. Exiting."; exit 1; fi

echo -e "\n--- All Kubernetes resources applied successfully! ---"
