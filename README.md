### How to run

- Start all the flask servers.
- Open frontend.html and put +14251000000 in the input and you will get response and logs.


In this version we are adding three Versions of Auth server For testing 
- v1
- v2
- v3

### v1
- Here we are assuming that based on Network Based Authentication the Mobile Number asscoiated to the 
user decive is fixed and is : 14251000000
- Using the frontend you can send any number you like , which will be compared against the fixed phone number.
- This was the initial version in Which main Focus was flow of token, Code Challenge , Code Verify etc. 


### v2
- Here we Assume a FIX IP ADDRESS which is : 192.168.0.2 (we Assume that we have IP Address From wherer the Request is Coming From)
- Then we try to get MSISDN based on IP ADDRESS
- For that we send request to ATSGATEWAY and from SYSLOG get the Private IP Address based on Public IP
- Then again with another request to ATSGATEWAY we get MSISDN based on Private IP
- Then we assign token Against This Number.

### v3
- It is similar to v2 but one step ahead. Here we Assume that the Request Header do have the Actual IP. 
- We take the IP from the request Header and then perform the same step as v2



------------------------------------------------------------