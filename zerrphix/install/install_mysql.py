# -*- coding: utf-8 -*-
install_mysql_bash = \
"""#!/bin/bash
set -e
log_file='::temp_dir::::os_sep::zp_mysql_install.log'

export PATH=$PATH:/usr/local/bin:/usr/bin:/bin

function log(){
	log_date=$(date '+%Y-%m-%d %H:%M:%S')
	(>&1 echo "$log_date $1")
	echo "$log_date $1" >> $log_file
}
install_mysql_server=::install_mysql_server::
drop_db_if_exists=::drop_db_if_exists::
mysql_root_password=$1
[ -f $log_file ] && rm -- $log_file
log "Script Started"
if [ $install_mysql_server -eq 1 ]; then
    log "Updating apt cache. Please wait (this can take several minutes)."
    sudo apt-get update >> $log_file 2>&1
    if [ $? -eq 0 ]; then
	    log "Updated apt-cache successfully"
	    export DEBIAN_FRONTEND=noninteractive  >> $log_file 2>&1
	    log "Downloading and installing mysql-server. Please wait (this can take several minutes)."
	    sudo -E apt-get -q -y install mysql-server  >> $log_file 2>&1
	    if [ $? -eq 0 ]; then
		    log "installed mysql-server"
		    sudo mysqladmin -u root password $mysql_root_password
		    #sudo mysql -u root -e "use mysql; update user set plugin='' where User='root'; flush privileges;"
        else
            log "failed to install mysql-server with exit code $? Please see log file $log_file"
            exit 1
        fi
    else
        log "failed to update apt cache with exit code $? Please see log file $log_file"
        exit 1
    fi
else
    log "Not going to install mysql server as per user choice. Script assuming a mysql server is running with root plugin set to unix socket."
fi
if [ $drop_db_if_exists -eq 1 ]; then
    log "Dropping ::db_name:: if it exists and creating it"
    sudo mysql -u root < ::temp_dir::::os_sep::zerrphix_first_install_drop_db.sql
    if [ $? -eq 0 ]; then
        log "Successfully dropped db ::db_name:: if it existed"
    else
        log "Failed to drop db ::db_name::"
        exit 1
    fi
fi
log "Trying to create db ::db_name:: this will do nothing if the db already exists"
sudo mysql -u root < ::temp_dir::::os_sep::zerrphix_first_install_create_db.sql
if [ $? -eq 0 ]; then
    log "Creating Tables"
    sudo mysql -u root ::db_name:: < ::temp_dir::::os_sep::zerrphix_first_install_create_tables.sql
    if [ $? -eq 0 ]; then
        log "Populating Tables"
        sudo mysql -u root ::db_name:: < ::temp_dir::::os_sep::zerrphix_first_install_populate_tables.sql
        if [ $? -eq 0 ]; then
            log "Running Post Populate"
            sudo mysql -u root ::db_name:: < ::temp_dir::::os_sep::zerrphix_first_install_post_populate.sql
            if [ $? -eq 0 ]; then
                log "Adding zerrphix admin/dune user"
                sudo mysql -u root ::db_name:: < ::temp_dir::::os_sep::zerrphix_first_install_add_user.sql
                if [ $? -eq 0 ]; then
                    log "Adding zerrphix app db user"
                    sudo mysql -u root < ::temp_dir::::os_sep::zerrphix_first_install_add_mysql_user.sql
                    if [ $? -eq 0 ]; then
                        log "Script completed successfully."
                        exit 0
                    else
                        log "Failed to add mysql user. Please see log file $log_file"
                        exit 1
                    fi
                else
                    log "Failed to add db ::db_name:: user. Please see log file $log_file"
                    exit 1
                fi
            else
                log "Failed to post populate. tables Please see log file $log_file"
                exit 1
            fi
        else
            log "Failed to populate tables. Please see log file $log_file"
            exit 1
        fi
    else
        log "Failed to Create Tables. Please see log file $log_file"
    fi
else
    log "Failed to create db. Please see log file $log_file"
fi
"""