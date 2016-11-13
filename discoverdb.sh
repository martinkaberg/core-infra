#!/usr/bin/env bash

cat > /var/www/html/aws_prepend.php <<EOL
<?php
// Valid constant names
define("__AWS_RDS_HOST__",     "${DbHost}");
define("__AWS_RDS_PORT__",    "${DbPort}");
define("__AWS_REGION__",    "${AWSRegion}");
define("__AWS_CFN_STACK__",    "${AWSStackName}");
?>
EOL
#sed -i  's/auto_prepend_file =/auto_prepend_file = \/var\/www\/html\/aws_prepend.php/g'   /etc/php5/apache2/php.ini
#service httpd restart

