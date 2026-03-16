-- Create the test database if it doesn't exist
CREATE DATABASE IF NOT EXISTS test_pod_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant all privileges on the test database to the pod user
GRANT ALL PRIVILEGES ON test_pod_db.* TO 'pod_user'@'%';

-- Grant CREATE and DROP globally so the test runner can create/destroy the test DB if needed
-- (Though we usually prefer reusing the existing one, Django's test runner might try to create one)
GRANT CREATE, DROP ON *.* TO 'pod_user'@'%';

FLUSH PRIVILEGES;
