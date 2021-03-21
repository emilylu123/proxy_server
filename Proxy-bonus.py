# Bonus Questions
# 1 Check the Expires header of cached objects to determine if a new copy is needed from the origin server instead of just sending back the cached copy (2 marks)
# 2 Respond correctly to the cache-control header max-age=<seconds> sent by the client. (2 marks)
# 3 The current proxy only handles URLs of the form hostname/file Add the ability to handle origin server ports that are specified in the URL, i.e. hostname:portnumber/file (2 marks)

# Include the libraries for socket and system calls
import socket
import sys
import os
import argparse
import re
# for bonus question
import datetime
import time

# 1MB buffer size
BUFFER_SIZE = 1000000

parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()

# Create a server socket, bind it to a port and start listening
# The server IP is in args.hostname and the port is in args.port
# bind() accepts an integer only
# You can use int(string) to convert a string to an integer
# ~~~~ INSERT CODE ~~~~
HOST = args.hostname
PORT = int(args.port)
# ~~~~ END CODE INSERT ~~~~

try:
    # Create a server socket
    # ~~~~ INSERT CODE ~~~~
    proxySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # ~~~~ END CODE INSERT ~~~~
    print 'Connected socket'
except:
    print 'Failed to create socket'
    sys.exit()

try:
    # Bind the the server socket to a host and port
    # ~~~~ INSERT CODE ~~~~
    proxySocket.bind((HOST, PORT))
    # ~~~~ END CODE INSERT ~~~~
    print 'Port is bound'
except:
    print 'Port is in use'
    sys.exit()

try:
    # Listen on the server socket
    # ~~~~ INSERT CODE ~~~~
    proxySocket.listen(100)
    # ~~~~ END CODE INSERT ~~~~
    print 'Listening to socket'
except:
    print 'Failed to listen'
    sys.exit()

while True:
    print 'Waiting connection...'

    clientSocket = None
    try:
        # Accept connection from client and store in the clientSocket
        # ~~~~ INSERT CODE ~~~~
        (clientSocket, address) = proxySocket.accept()
        # ~~~~ END CODE INSERT ~~~~
        print 'Received a connection from:', args.hostname

    except:
        print 'Failed to accept connection'
        sys.exit()

    message = 'METHOD URI VERSION'
    # Get request from client
    # and store it in message
    # ~~~~ INSERT CODE ~~~~
    message = clientSocket.recv(BUFFER_SIZE)
    # ~~~~ END CODE INSERT ~~~~

    print 'Received request:'
    print '< ' + message

    # Extract the parts of the HTTP request line from the given message
    requestParts = message.split()
    method = requestParts[0]
    URI = requestParts[1]
    version = requestParts[2]

    print 'Method:\t\t' + method
    print 'URI:\t\t' + URI
    print 'Version:\t' + version
    print ''

    # Remove http protocol from the URI
    URI = re.sub('^(/?)http(s?)://', '', URI, 1)

    # Remove parent directory changes - security
    URI = URI.replace('/..', '')

    # Split hostname from resource
    resourceParts = URI.split('/', 1)
    hostname = resourceParts[0]
    resource = '/'

    print "\n********* Bonus 3: Handle URLs with port number *********\n"
    portNumber = 80
    hostOrigin = hostname

    if ':' in hostname:
        print ">>> Handle URL with port number"
        (hostOrigin, portOrigin) = hostname.split(':')
        portNumber = int(portOrigin)
    else:
        print ">>> No need to Handle URL"

    print ">>> HOST:", hostOrigin, "\n>>> PORT:", portNumber
    print "\n******************* End *** Bonus 3 **********************\n"

    if len(resourceParts) == 2:
        # Resource is absolute URI with hostname and resource
        resource = resource + resourceParts[1]

    print 'Requested Resource:\t' + resource

    cacheLocation = './' + hostname + resource
    if cacheLocation.endswith('/'):
        cacheLocation = cacheLocation + 'default'

    print 'Cache location:\t\t' + cacheLocation

    fileExists = os.path.isfile(cacheLocation)

    try:
        # Bonus Question 2
        print "\n********* Bonus 2: Check cache-control header *********\n"
        print ">>> Checking max-age in clients request "
        # get cache creat time from local cache
        # will go to exceptions if there is no cache file find
        cacheTime = os.stat(cacheLocation).st_ctime
        now = time.time()
        freshnessAge = now - cacheTime

        isExpired = False
        maxAge = 0
        control = ""

        if "Cache-Control" in message:
            clientRequest = message.split('\n')
            for data in clientRequest:
                if "Cache-Control" in data:
                    control = data.split(':')[1]
                    print ">>> Cache-Control:\t", control

                    if "no-cache" in control:
                        isExpired = True
                        print(">>> No Cache is allowed")
                        break

                    if "max-age" in control:
                        for str in control.split(','):
                            if 'max-age' in str:
                                maxAge = int(str.replace('max-age=', '').strip())
                                print ">>> Max-Age =", maxAge
                                break

                        if maxAge <= 0:
                            isExpired = True
                            print ">>> Cache is expired due to Max-Age =", maxAge
                        elif freshnessAge > maxAge:
                            print ">>> Current Time:", now
                            print ">>> Cache Time:", cacheTime
                            print ">>> calculate Cache Freshness Age =", freshnessAge
                            print ">>> Cache is expired by checking freshness Age", freshnessAge, ">", maxAge
                            isExpired = True
                        else:
                            print ">>> Cache is Fresh by checking freshness Age", freshnessAge, "<=", maxAge

        else:
            print "No cache-control header is found in clients request"

        # remove local cache if tag isExpired is True, where freshness age > max-age
        # this will let proxy request new copy from origin server
        if isExpired:
            print(">>> Cache File is Expired")
            # remove local stale cache
            # if fileExists:
            os.remove(cacheLocation)
            fileExists = False
            print ">>> Stale Cache <", cacheLocation + "> has been removed."
            print ">>> Proxy will request latest copy from origin server"
        print "\n***************** End *** Bonus 2 ********************\n"

        # Check weather the file exist in the cache
        cacheFile = open(cacheLocation, "r")
        outputdata = cacheFile.readlines()

        print 'Cache hit! Loading from cache file: ' + cacheLocation
        # ProxyServer finds a cache hit

        # Bonus Question 1 - check Expire header of cached objects
        print "\n********* Bonus 1: Check Expires header *********\n"
        print ">>> Checking cache expires header"
        # get expire date from cache "Expires:" item
        expireDate=""
        for data in outputdata:
            if "Expires" in data:
                findDate = data.strip()[14:]
                expireDate = datetime.datetime.strptime(findDate, "%d %b %Y %H:%M:%S %Z")
        print ">>> Expires:\t", (expireDate)

        # get current date
        currentDate = datetime.datetime.utcnow()
        print ">>> Current:\t", currentDate

        # compare two date to see if cache file is stale
        # tag isExpired
        if currentDate > expireDate:
            isExpired = True
        else:
            print(">>> Cache File is Fresh")

        if isExpired:
            print(">>> Cache File is Expired")
            # remove local stale cache
            os.remove(cacheLocation)
            fileExists = os.path.isfile(cacheLocation)
            print ">>> File exists", fileExists
            print ">>> Stale Cache <", cacheLocation + "> has been removed."
            print ">>> Request latest copy from origin server"
        print "\n***************** End *** Bonus 1 ********************\n"
        # raise an exception to request new copy
        raise Exception("Cache File is Expired")

        # Send back contents of cached file
        # ~~~~ INSERT CODE ~~~~
        out = ''.join(outputdata)
        # handle internal server error here
        if out.strip() in (None, ''):
            print "\n>>> Error in loading cache file: Empty file is found\n"

            clientResponse = 'HTTP/1.1 404 Not Found'
            clientSocket.sendall(clientResponse + "\r\n\r\n")
            print '>>> Sending to the client:'
            print ">>> ", clientResponse, "\n"

            if os.path.isfile:
                os.remove(cacheLocation)
                fileExists=false
                print ">>> ", cacheLocation + " has been removed."

            print ">>> Please reload the page again later.\n"

        else:
            clientSocket.sendall(out + "\r\n\r\n")
        # ~~~~ END CODE INSERT ~~~~

        cacheFile.close()

    # Error handling for file not found in cache
    # bonus to catch all excepts, instead of except IOError only
    except Exception as e:
        # print ">>> ", e
        if fileExists:
            clientResponse = ''
            # If we get here, the file exists but the proxy can't open or read it
            # What would be the appropriate status code and message to send to client?
            # store the value in clientResponse
            # ~~~~ INSERT CODE ~~~~
            #  handle internal server error - cache file exists, but can't be open or read
            print "> Error in loading cacheFile: Can't Open or Read the Cache File"
            print '>'
            #  delete local cash files
            if os.path.isfile:
                os.remove(cacheLocation)
                print "> ", cacheLocation + " has been removed."
                print '>'

            print "> Please reload the page again later."
            print '>'

            clientResponse = 'HTTP/1.1 404 Not Found'

            # ~~~~ END CODE INSERT ~~~~

            print 'Sending to the client:'
            print '> ' + clientResponse
            print '>'
            clientSocket.sendall(clientResponse + "\r\n\r\n")

        else:
            originServerSocket = None
            # Create a socket to connect to origin server
            # and store in originServerSocket
            # ~~~~ INSERT CODE ~~~~
            originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # ~~~~ END CODE INSERT ~~~~

            print 'Connecting to:\t\t' + hostname + '\n'
            try:
                # Get the IP address for a hostname
                address = socket.gethostbyname(hostOrigin)

                # Connect to the origin server
                # ~~~~ INSERT CODE ~~~~
                # Bonus 3
                # handle hostname with portnumber: change (hostname,80) to (hostOrigin, portNumber)
                originServerSocket.connect((hostOrigin, portNumber))
                # ~~~~ END CODE INSERT ~~~~

                print 'Connected to origin Server'

                # Create a file object associated with this socket
                # This lets us use file function calls
                originServerFileObj = originServerSocket.makefile('+', 0)

                originServerRequest = ''
                originServerRequestHeader = ''
                # Create origin server request line and headers to send
                # and store in originServerRequestHeader and originServerRequest
                # originServerRequest is the first line in the request and
                # originServerRequestHeader is the second line in the request
                # ~~~~ INSERT CODE ~~~~
                originServerRequest = method + ' ' + resource + ' ' + version
                originServerRequestHeader = 'Host: ' + hostname
                # ~~~~ END CODE INSERT ~~~~

                # Construct the request to send to the origin server
                request = originServerRequest + '\r\n' + originServerRequestHeader + '\r\n\r\n'

                # Request the web resource from origin server
                print 'Forwarding request to origin server:'
                for line in request.split('\r\n'):
                    print '> ' + line

                try:
                    originServerSocket.sendall(request)
                except socket.error:
                    print 'Send failed'
                    sys.exit()

                originServerFileObj.write(request)

                # Get the response from the origin server
                # ~~~~ INSERT CODE ~~~~
                response = ''
                while True:
                    data = originServerSocket.recv(BUFFER_SIZE)
                    if not data:
                        break
                    response += data
                # ~~~~ END CODE INSERT ~~~~

                # Send the response to the client
                # ~~~~ INSERT CODE ~~~~
                clientSocket.send(response)
                # ~~~~ END CODE INSERT ~~~~

                # finished sending to origin server - shutdown socket writes
                originServerSocket.shutdown(socket.SHUT_WR)

                print 'Request sent to origin server\n'

                # Create a new file in the cache for the requested file.
                # Also send the response in the buffer to client socket
                # and the corresponding file in the cache
                cacheDir, file = os.path.split(cacheLocation)
                print 'cached directory ' + cacheDir
                if not os.path.exists(cacheDir):
                    os.makedirs(cacheDir)
                cacheFile = open(cacheLocation, 'wb')

                # Save origin server response in the cache file
                # ~~~~ INSERT CODE ~~~~
                cacheFile.write(response)
                # ~~~~ END CODE INSERT ~~~~

                print 'done sending'
                originServerSocket.close()
                cacheFile.close()
                print 'cache file closed'
                clientSocket.shutdown(socket.SHUT_WR)
                print 'client socket shutdown for writing'
            except IOError, (value, message):
                print 'origin server request failed. ' + message
    try:
        clientSocket.close()
    except:
        print 'Failed to close client socket'
