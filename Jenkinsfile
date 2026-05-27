pipeline {
    agent any
    
    environment {
        ENGINE_URL = 'http://grs-engine:8080'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Determine Target Slot') {
            steps {
                script {
                    env.COMMIT_SHA = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    echo "Current repository commit: ${env.COMMIT_SHA}"
                    
                    // Check blue version
                    def blueVersion = 'none'
                    try {
                        blueVersion = sh(script: "docker exec grs-app-blue sh -c 'echo \$APP_VERSION'", returnStdout: true).trim()
                    } catch (Exception e) {
                        echo "Could not fetch blue version from container (likely not running): ${e.getMessage()}"
                        blueVersion = 'none'
                    }
                    echo "Current Blue container version: ${blueVersion}"
                    
                    if (blueVersion == 'v1' || blueVersion == 'none') {
                        env.TARGET_COLOR = 'blue'
                        echo "Target slot determined: blue (bootstrapping latest commit)"
                    } else if (blueVersion == env.COMMIT_SHA) {
                        env.TARGET_COLOR = 'skip'
                        echo "Target slot determined: skip (Blue is already running the latest commit)"
                    } else {
                        env.TARGET_COLOR = 'green'
                        echo "Target slot determined: green (new commit candidate)"
                    }
                }
            }
        }
        
        stage('Build & Deploy Blue') {
            when {
                environment name: 'TARGET_COLOR', value: 'blue'
            }
            steps {
                script {
                    echo "Building new image for app-blue with tag ${env.COMMIT_SHA}..."
                    sh "docker build -t grs/app-blue:${env.COMMIT_SHA} -f Dockerfile ."
                    
                    echo "Stopping existing grs-app-blue container..."
                    sh "docker stop grs-app-blue || true"
                    sh "docker rm grs-app-blue || true"
                    
                    echo "Starting new grs-app-blue container with version ${env.COMMIT_SHA}..."
                    sh """
                        docker run -d \
                          --name grs-app-blue \
                          --network grs-network \
                          -p 5001:5000 \
                          -e APP_COLOR=blue \
                          -e APP_VERSION=${env.COMMIT_SHA} \
                          -e SIMULATED_LATENCY_MS=25 \
                          -e SIMULATED_ERROR_RATE=0.0 \
                          grs/app-blue:${env.COMMIT_SHA}
                    """
                    
                    echo "Verifying blue deployment health..."
                    sh """
                        for i in {1..12}; do
                            if curl -fsS http://grs-app-blue:5000/health; then
                                echo "grs-app-blue is healthy!"
                                exit 0
                            fi
                            echo "Waiting for grs-app-blue to start..."
                            sleep 2
                        done
                        echo "grs-app-blue failed health check!"
                        exit 1
                    """
                    echo "Ensuring grs-nginx is running..."
                    sh "docker start grs-nginx || true"
                }
            }
        }
        
        stage('Build & Deploy Green') {
            when {
                environment name: 'TARGET_COLOR', value: 'green'
            }
            steps {
                script {
                    echo "Building new image for app-green with tag ${env.COMMIT_SHA}..."
                    sh "docker build -t grs/app-green:${env.COMMIT_SHA} -f Dockerfile ."
                    
                    echo "Stopping existing grs-app-green container..."
                    sh "docker stop grs-app-green || true"
                    sh "docker rm grs-app-green || true"
                    
                    echo "Starting new grs-app-green container with version ${env.COMMIT_SHA}..."
                    sh """
                        docker run -d \
                          --name grs-app-green \
                          --network grs-network \
                          -p 5002:5000 \
                          -e APP_COLOR=green \
                          -e APP_VERSION=${env.COMMIT_SHA} \
                          -e SIMULATED_LATENCY_MS=35 \
                          -e SIMULATED_ERROR_RATE=0.0 \
                          grs/app-green:${env.COMMIT_SHA}
                    """
                    
                    echo "Verifying green deployment health..."
                    sh """
                        for i in {1..12}; do
                            if curl -fsS http://grs-app-green:5000/health; then
                                echo "grs-app-green is healthy!"
                                exit 0
                            fi
                            echo "Waiting for grs-app-green to start..."
                            sleep 2
                        done
                        echo "grs-app-green failed health check!"
                        exit 1
                    """
                }
            }
        }
        
        stage('Trigger Promotion') {
            when {
                environment name: 'TARGET_COLOR', value: 'green'
            }
            steps {
                script {
                    echo "Triggering blue-green promotion on GRS Engine..."
                    sh "curl -X POST ${env.ENGINE_URL}/promote"
                }
            }
        }
    }
}
