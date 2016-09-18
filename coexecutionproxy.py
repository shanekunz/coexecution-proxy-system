import cx_Oracle
import mysocket
import socket
import uuid
import random
import select
import sys
import datetime

class NoCoexecutioner(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Denied(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)    

portNumber = int(raw_input("Please enter port number to start server: "))
print "Starting CoExecution Proxy..."
connection = cx_Oracle.connect("Coexecute01/DePaul123@rasinsrv06.cstcis.cti.depaul.edu:1521/Oracle12c")
#make 2nd arg threaded=True if multithreading is needed
print "CoEx Server connected to database successfully. Waiting for connections..."

socket_to_executors = {}
executors_to_socket = {}
socket_to_coexecutioners = {}
coexecutioners_to_socket = {}
#These are dictionaries that have the key as the username and the value as the socket for that user
requests = {}
#requests in the form {'Executor':['SELECT * FROM PATIENT',{'PATIENT':False},'table.sensitivefield',queryID]}
# where False means not yet approved
permissions = {}
#Permissions are {'Coexecutioner':['table coexecutioner can allow access to']}
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('', portNumber))
serversocket.listen(5)
#Start the server's socket

cursor=connection.cursor()


socket_list=[serversocket]
while True:
    ready_to_read,ready_to_write,in_error = select.select(socket_list,[],[],0)
    for s in ready_to_read:
    #Select grabs any sockets in the list that have sent readable data
        if s == serversocket:
        #If the serversocket is readable it means a client connected, so accept the connection
            conn, addr = serversocket.accept()
            sock = mysocket.MySocket(conn)
            userType = sock.receive()
            userName = sock.receive()
            #When a user connects receive the type of user they are and their name
            if userType == 'executor':
                socket_to_executors[conn] = userName
                executors_to_socket[userName] = conn
                socket_list.append(conn)
                print "Executor " + userName + " connected"
                #Add the executors socket to the dictionary. And start a thread that receives and processes
                # queries sent by the executors
            elif userType == 'coexecutioner':
                socket_to_coexecutioners[conn] = userName
                coexecutioners_to_socket[userName] = conn
                socket_list.append(conn)
                cursor.execute("SELECT TABLE_NAME FROM CAN_GIVE_PERMISSION WHERE USER_NAME = '"+userName+"'")
                tables=[]
                for table in cursor.fetchall():
                    tables.append(table[0])
                for requestName in requests:
                    sending_request=False
                    relevant_sensitive_fields = ''
                    for table_needing_approval in requests[requestName][1]:
                        if not requests[requestName][1][table_needing_approval]:
                            if table_needing_approval in tables:
                                sending_request=True
                                for sensitive_field in requests[requestName][2][table_needing_approval]:
                                    relevant_sensitive_fields = (relevant_sensitive_fields+
                                                                 table_needing_approval+'.'+sensitive_field+', ')
                    if sending_request:
                        relevant_sensitive_fields = relevant_sensitive_fields[:-2]
                        sock.send('Add|'+ requests[requestName][4] +'|'+ requests[requestName][5]+'|'
                                  +requests[requestName][0] +'|'+ relevant_sensitive_fields)
                print "CoExecutioner " + userName + " connected"
                #Add the coexecutioners socket to the dictionary. Don't need to start a thread because the
                # executor_worker thread will start ask_coex_worker threads when permission to access
                # a table or field is requested.
        if s in socket_to_coexecutioners.keys():
            try:
                name = socket_to_coexecutioners[s]
                sock = mysocket.MySocket(s)
                #Grab the name and socket of the coexecutioner
                data=sock.receive().split('|')
                request=requests[data[1]+'|'+data[2]]
                #Coexecutioners send Approve and Deny messages in the form "Approve|executor's name|Query number"
                if data[0] == 'Approve':
                    allowed = True
                    approved_tables=set()
                    previously_approved_tables=set()
                    tables_needing_approval = request[1]
                    all_tables_set = set(request[1].keys())
                    query = request[0]
                    cursor.execute("SELECT USER_NAME, TABLE_NAME FROM CAN_GIVE_PERMISSION")
                    for row in cursor.fetchall():
                        if row[0] in permissions:
                            permissions[row[0]].append(row[1])
                        else:
                            permissions[row[0]]=[row[1]]
                    #Fill a permissions dictionary with coexecutioner names as keys and the values as a list of the tables
                    #they can give access to
                    for table in tables_needing_approval:
                        if not tables_needing_approval[table]:
                            if table in permissions[name]:
                            #If current table has not yet been approved and the coexecutioner has perission to approve
                                approved_tables.add(table)
                                tables_needing_approval[table]=True
                                # Mark it as approved
                            else:
                                allowed = False
                                #Getting here mean a table has not yet been approved and the approving coexecutioner
                                # doesn't have permission to approve, so set allowed to false so the query isn't executed
                        else:
                            previously_approved_tables.add(table)
                            approved_tables.add(table)
                            #Getting here means the current table has already been approved
                    for n in permissions:
                        if n in coexecutioners_to_socket:
                            #If this coexecutioner is currently connected
                            permission_set = set(permissions[n])
                            can_give_permission = permission_set & all_tables_set
                            #Get all the coexecutioner permissions relevant to this request
                            if approved_tables>=can_give_permission:
                                #If now the approved tables are a superset of the coexecutioner's permissions...
                                no_longer_can_give_permission = mysocket.MySocket(coexecutioners_to_socket[n])
                                no_longer_can_give_permission.send('Remove|'+data[1]+'|'+data[2])
                                # then tell them to remove the request because they can no longer help the request
                                # by approving given the state of their permissions
                    f = open('log.txt', 'a')
                    f.write('Coexecutioner approved executor '+data[1]+"'s"+' query "'+request[0]+'". query id:'+
                            request[3]+' time:'+datetime.datetime.now().strftime("%m-%d-%Y %I:%M:%S%p")+'\n')
                    f.close()
                    if allowed:
                        #If the coexecutioner's approval fulfilling
                        print "Executing query"
                        cursor.execute(query)
                        f=open('log.txt', 'a')
                        f.write('Executor '+data[1]+' received sufficient approval to run query "'+request[0]+
                                '". query id:'+request[3]+' time:'+datetime.datetime.now().strftime("%m-%d-%Y %I:%M:%S%p")+'\n')
                        f.close()
                        queryText=''
                        try:
                            count = 0
                            for row in cursor:
                                if count >= 100:
                                    queryText='Showing only first 100 rows:\n'+queryText
                                    break
                                rowText = '| '
                                for item in row:
                                    rowText=rowText+str(item)+" | "
                                queryText=queryText+rowText+'\n'
                                count += 1
                            print 'Request:'+str(request)+' has been approved'
                        except cx_Oracle.InterfaceError as e:
                            queryText='Query was sucessfully run.'
                            connection.commit()
                        executor_sock = mysocket.MySocket(executors_to_socket[data[1]])
                        executor_sock.send(data[2]+'|!|'+queryText)
                        del request #try requests[data[1]] if no working
                elif data[0] == 'Deny':
                #Coexecutioner Denied an executors request
                    executor_socket = mysocket.MySocket(executors_to_socket[data[1]])
                    executor_socket.send(data[2]+"|!|ERROR: A coexecutioner denied giving you table data")
                    f=open('log.txt', 'a')
                    f.write('Coexecutioner denied executor '+data[1]+"'s"+' query "'+request[0]+'". query id:'+
                            request[3]+' time:'+datetime.datetime.now().strftime("%m-%d-%Y %I:%M:%S%p")+'\n')
                    f.close()
                    #Tell the executor that a coexecutioner said 'no' to giving access to that table
                    for deny_sock in socket_to_coexecutioners:
                        coex_sock = mysocket.MySocket(deny_sock)
                        coex_sock.send('Remove|'+data[1]+'|'+data[2])
                    #Tell all coexecutioners to remove the executor's request since it has been denied
                    del requests[data[1]+'|'+data[2]]
                    #Delete request from the requests dictionary
            except:
                socket_list.remove(s)
                del socket_to_coexecutioners[s]
                del coexecutioners_to_socket[name]
                print sys.exc_info()[0]
                print "Disconnected "+name+" because of an error"
        if s in socket_to_executors.keys():
        #If the readable socket is coming from an executor, then they sent in a query
            name = socket_to_executors[s]
            sock = mysocket.MySocket(s)
            queryNumber='0'
            #Get the name and socket of the executor
            try:
                data = sock.receive().split('|')
                queryNumber = data[0]
                query = data[1]
                identifier = str(uuid.uuid4())[:30] #Statement id in oracle can only be 30 characters long
                cursor.execute("EXPLAIN PLAN SET STATEMENT_ID = '"+identifier+"' FOR "+query)
                cursor.execute("SELECT OPERATION, OBJECT_NAME, FILTER_PREDICATES, PROJECTION "+
                                 "FROM PLAN_TABLE WHERE STATEMENT_ID = '"+identifier+"'")
                #Grabs execution plan for the query the executor sent
                query_type=''
                coexecutioners_set=set()
                table_fields={}
                tables_set=set()
                rows = cursor.fetchall()
                for row in rows:
                    operation = row[0]
                    if 'STATEMENT' in operation:
                        query_type = operation.split()[0]
                        break
                #Gets what type of statement the query is, e.g. SELECT, INSERT, ...
                if query_type == 'SELECT' or query_type == 'UPDATE':
                    for row in rows:
                        op, table, filt, proj = row
                        #Goes through each row of the execution plan
                        if 'TABLE ACCESS' == op:
                            #When the operation column is 'TABLE ACCESS' then the execution table
                            #row includes the table name and the filter predicates and projection
                            #fields that are trying to be accessed
                            cursor.execute("SELECT count(*) FROM HAVE_PERMISSION HP"+
                                            " WHERE '"+name+"' = HP.USER_NAME AND '"+table+"' = HP.TABLE_NAME")
                            #Checks if the executor has permission to access the table from the
                            #HAVE_PERMISSION table in the database
                            if cursor.next()[0] == 0:
                                #If database returns a count of zero than the executor is not listed as having
                                #permission to the table in the HAVE_PERMISSION table.
                                print name+" does not have permission to access "+table+" in the HAVE_PERMISSION table"
                                if filt is None:
                                    filt = set()
                                    #If no WHERE clause was in the query then filter predicates are None
                                    #so filt should just be an empty set when the filt and proj are joined
                                else:
                                    filt = set(filt.split('"')[1::2])
                                proj = set(proj.split('"')[1::2])
                                cursor.execute("select COLUMN_NAME from USER_TAB_COLUMNS where table_name = '"+table+"'")
                                table_columns = set()
                                for field in cursor.fetchall():
                                    table_columns.add(field[0])
                                filt_pred_and_proj = (filt | proj) & table_columns
                                for field in filt_pred_and_proj:
                                    cursor.execute("SELECT count(*) FROM SENSITIVE_FIELDS SF WHERE "+
                                                   "SF.COEX_TABLE = '"+table+"' AND SF.SENSITIVE_FIELD = '"+field+"'")
                                    #Goes through each field and checks the database to see if it's a sensitive
                                    # field for that for that table.
                                    if cursor.next()[0] > 0:
                                        #If database returns a count of 1 or greater than it's a sensitive field
                                        # in the SENSITIVE_FIELDS table.
                                        if table not in table_fields:
                                            table_fields[table]=[field]
                                        else:
                                            table_fields[table].append(field)
                                        tables_set.add(table)
                                        print "field "+field+" in table "+table+" is a sensitive field"
                                        cursor.execute("SELECT USER_NAME FROM CAN_GIVE_PERMISSION CGP WHERE "+
                                                       "CGP.TABLE_NAME = '"+table+"'")
                                        onlineCoexecutioners=[]
                                        for coexecutioner in cursor.fetchall():
                                            if coexecutioner[0] in coexecutioners_to_socket:
                                                onlineCoexecutioners.append(coexecutioner[0])
                                        #Grabs all the coexecutioners from the CAN_GIVE_PERMISSION table in the
                                        # database and adds their socket and name to a list if that coexecutioner
                                        # connected to the server.
                                        if not onlineCoexecutioners:
                                            raise NoCoexecutioner(table)
                                        #If no coexecutioner is online that can give access to that table then
                                        # raise an error.
                                        else:
                                            selected = set(onlineCoexecutioners)
                                            coexecutioners_set = coexecutioners_set | selected 
                                    else:
                                        print "field "+field+" is not sensitive"
                            else:
                               print name+" has permission to access "+table
                elif query_type == 'INSERT' or query_type == 'DELETE':
                    for row in rows:
                        op, table, filt, proj = row
                        if 'LOAD TABLE CONVENTIONAL' == op or 'TABLE ACCESS' == op:
                            cursor.execute("SELECT count(*) FROM HAVE_PERMISSION HP"+
                                            " WHERE '"+name+"' = HP.USER_NAME AND '"+table+"' = HP.TABLE_NAME")
                            if cursor.next()[0] == 0:
                                print (name+" does not have permission in the HAVE_PERMISSION table"+
                                       " to insert into "+table)
                                cursor.execute("select COLUMN_NAME from USER_TAB_COLUMNS where table_name = '"+table+"'")
                                for field in cursor.fetchall():
                                    field=field[0]
                                    cursor.execute("SELECT count(*) FROM SENSITIVE_FIELDS SF WHERE "+
                                                   "SF.COEX_TABLE = '"+table+"' AND SF.SENSITIVE_FIELD = '"+field+"'")
                                    #Goes through each field and checks the database to see if it's a sensitive
                                    # field for that for that table.
                                    if cursor.next()[0] > 0:
                                        if table not in table_fields:
                                            table_fields[table]=[field]
                                        else:
                                            table_fields[table].append(field)
                                        tables_set.add(table)
                                        cursor.execute("SELECT USER_NAME FROM CAN_GIVE_PERMISSION CGP WHERE "+
                                                       "CGP.TABLE_NAME = '"+table+"'")
                                        onlineCoexecutioners=[]
                                        for coexecutioner in cursor.fetchall():
                                            if coexecutioner[0] in coexecutioners_to_socket:
                                                onlineCoexecutioners.append(coexecutioner[0])
                                        if not onlineCoexecutioners:
                                           raise NoCoexecutioner(table)
                                        else:
                                            selected = set(onlineCoexecutioners)
                                            coexecutioners_set = coexecutioners_set | selected
                            else:
                                print name+" has permission to insert into "+table
                if query_type == 'SELECT' or query_type == 'DELETE' or query_type == 'UPDATE' or query_type == 'INSERT':
                    if coexecutioners_set:
                        print "Notifying coexecutioners:"+str(coexecutioners_set)+" of the query:"+query
                        #Something is in the set, that means the executor didn't have permission to
                        # access a table or field, and coexecutioners in the set will be notified of the request
                        tables_fields_string = ''
                        table_boolean_dict={}
                        for table in tables_set:
                            table_boolean_dict[table] = False
                        for table in table_fields:
                            for field in table_fields[table]:
                                tables_fields_string = tables_fields_string+table+'.'+field+", "
                        tables_fields_string = tables_fields_string[:-2]
                        #Build a dictionary and string of the restricted tables for the request
                        for coexecutioner in coexecutioners_set:
                            relevant_string = ''
                            cursor.execute("SELECT TABLE_NAME FROM CAN_GIVE_PERMISSION WHERE USER_NAME = '"+coexecutioner+"'")
                            for table in cursor.fetchall():
                                if table[0] in table_fields:
                                    for field in table_fields[table[0]]:
                                        relevant_string = relevant_string+table[0]+'.'+field+", "
                            relevant_string = relevant_string[:-2]
                            coexecutioner_socket = mysocket.MySocket(coexecutioners_to_socket[coexecutioner])
                            coexecutioner_socket.send('Add|'+name+'|'+queryNumber+'|'+query+'|'+relevant_string)
                        requests[name+'|'+queryNumber] = [query,table_boolean_dict,table_fields,identifier,name,queryNumber]
                        sock.send(queryNumber+'|!|'+'Waiting on coexecutioners to allow access to fields: '+tables_fields_string)
                        f=open('log.txt', 'a')
                        f.write('Executor '+name+' submitted query "'+query+'" that requires coexecutioner approval. query id:'
                                +identifier+' time:'+datetime.datetime.now().strftime("%m-%d-%Y %I:%M:%S%p")+'\n')
                        f.close()
                        #Add the requests to all relevant coexecutioners, add request to dictionary, tell executor to wait
                    else:
                        #If no coexecutioners were in the set and an error wasn't raise, then there's no restrictions
                        # on the query and it is allow to execute
                        print "Executing query"
                        cursor.execute(query)
                        queryText=''
                        try:
                            count = 0
                            for row in cursor:
                                if count >= 100:
                                    queryText='Showing only first 100 rows:\n'+queryText
                                    break
                                rowText = '| '
                                for item in row:
                                    rowText=rowText+str(item)+" | "
                                queryText=queryText+rowText+'\n'
                                count += 1
                        except cx_Oracle.InterfaceError as e:
                            queryText='Query was sucessfully run.'
                            connection.commit()
                            print 'Committed'
                        sock.send(queryNumber+'|!|'+queryText)
                        #Send the executor all the rows of the query
                else:
                    sock.send(queryNumber+'|!|'+"ERROR: only SELECT, INSERT, UPDATE, AND DELETE statements are allowed")
            except NoCoexecutioner as e:
                print "No Coexecutioner available to allow access to "+e.value
                sock.send(queryNumber+'|!|'+"ERROR: No Coexecutioner available to allow access to "+e.value)
                #Tell the executor that no coexecutioner was available to give access to that table
            except cx_Oracle.DatabaseError:
                sock.send(queryNumber+'|!|'+"ERROR: there was a problem with your query")
            except:
                socket_list.remove(s)
                del socket_to_executors[s]
                del executors_to_socket[name]
                print sys.exc_info()[0]
                print "Disconnected "+name+" because of an error"
