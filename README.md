# Feed Amalgamator

This branch contains the initial version of the web application feed-amalgmator developed using Flask.

Please follow the instructions below to run the application:

1. Install Pycharm - https://www.jetbrains.com/pycharm/download/?section=windows. You can install any IDE that you like. But it is recommended to use Pycharm to keep the development environment clean.

2. Install Conda - https://www.anaconda.com/download/

3.  Create a new conda python environment using Python version 3.11.5.
    conda create -n [environment name here] python=3.11.5
    conda create --name [environment name here] --file requirements.txt

4.  Run flask --app feed_amalgamator init-db. This will run the SQL script and create the necessary tables for the application. 

5.  Put the client.ini file in instance director.

6.  Run flask --app feed_amalgamator run --debug . This opens the website in your browser. In debug you can make live changes in the code which will be reflected on to the website without having restart the server. 

