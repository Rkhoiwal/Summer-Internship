from flask import Flask,render_template
from sklearn.metrics import mean_squared_error
import MySQLdb as mysql
import math
import hashlib
import sys
import os

def list():
	conn=connect()
	rows=fetch_everything_from_table(conn,'data')
	close(conn)
	return render_template('test.html',rows = rows)


def copy_data_from_src_to_dest(src,dest):
	conn=connect()
	delete_everything_table(conn,dest)
	param=fetch_a_b_c_from_table(conn,src)
	insert_param_into_table(conn,dest,param)
	close(conn)
 	
def update():
	conn=connect()
	rows=fetch_everything_from_table(conn,'data2')
	close(conn)
	return render_template('test.html',rows = rows)

def hash(id):
	m=hashlib.md5()
	m.update('gdkjssaklhd14252e8967bvsvvc')
	m.update(str(id))
	return m.hexdigest()


def check_id(id):
	if int(hash(id),27)%11 == 0:
		return True
	else:
		return False	


def watermark(table_name):
	conn=connect()
	count=0
	params=[]
	bit_size=128
	mask=10
	#print "Watermarked Tuples"
	for i in range(1,10000):
		if check_id(i) == True:
			row = fetch_only_a_b_c_from_table(conn,table_name,i)
			#update_only_a_b_c_in_table(conn,table_name,i,1,1,1)
			a_old,b_old,c_old=row[0],row[1],row[2]
			a8_old,b8_old=a_old%bit_size,b_old%bit_size
			a_mod,b_mod=a_old-a8_old,b_old-b8_old

			lbefore=(a8_old+b8_old)/2
			hbefore=a8_old - b8_old

			hdash=2*hbefore+0

			g=(hdash+1)/2
			f=hdash/2
			
			anew8,bnew8=lbefore+g,lbefore-f
			if ((anew8>=0 and anew8<bit_size) and (bnew8>=0 and bnew8<bit_size)):
				a_new=a_mod+anew8
				b_new=b_mod+bnew8
				c_new=c_old|mask
				#print i,a_new,b_new,c_new
				params.append((a_new,b_new,c_new,i))
				count+=1
				#print i

	update_all_a_b_c_in_table(conn,table_name,params)			

	print "Total rows Updated %d"%count
	close(conn)
	

def reverse_watermark(table_name):
	conn=connect()
	count=0
	params=[]
	bit_size=128
	mask=10
	#print "Reverse Watermarked Tuples"
	for i in range(1,10000):
		if check_id(i) == True:
			row = fetch_only_a_b_c_from_table(conn,table_name,i)
			#update_only_a_b_c_in_table(conn,table_name,i,1,1,1)
			a_old,b_old,c_old=row[0],row[1],row[2]
			a8_old,b8_old=a_old%bit_size,b_old%bit_size
			a_mod,b_mod=a_old-a8_old,b_old-b8_old

			lbefore=(a8_old+b8_old)/2
			hbefore=a8_old - b8_old

			hdash=hbefore/2

			g=(hdash+1)/2
			f=hdash/2

			anew8,bnew8=lbefore+g,lbefore-f
			if ((c_old&10)==mask):
				a_new=a_mod+anew8
				b_new=b_mod+bnew8
				temp=sys.maxint
				c_new=c_old&(temp^mask)

				#print i,a_new,b_new,c_new
				params.append((a_new,b_new,c_new,i))
				count+=1
				#print i

	update_all_a_b_c_in_table(conn,table_name,params)			

	print "Total rows Updated %d"%count
	close(conn)		


def count_similarity(list1,list2):
	count=0;
	#print list1
	#print list2
	for i in range(0,9999):
		if (int(list1[i][0])==int(list2[i][0]))&(int(list1[i][1])==int(list2[i][1]))&(int(list1[i][2])==int(list2[i][2])):
			count+=1
			#print i+1

	per=(float(count)/9999)*100
	ans=9999-count
	print "Total tuples not matched %d "%(ans)
	return per		

def compare_tables(src,dest):
	conn=connect()
	list1=fetch_a_b_c_from_table(conn,src)
	list2=fetch_a_b_c_from_table(conn,dest)
	ans = count_similarity(list1,list2)
	print '\n'
	print "Percentage matched %f "%(ans)
	print "Mean Square Error " + str(mean_squared_error(list1,list2))
	# print "Root Mean Square Error " + str(math.sqrt(mean_squared_error(list1,list2)))

def generate_parameters():#unset 2nd and 4th bit
	params=[]
	for i in range(1,10000):
		a=random.randint(1,10000)
		b=random.randint(1,10000)
		c=random.randint(1,10000)
		temp=sys.maxint
		c=c&(temp^2)#unsetting 2nd bit
		c=c&(temp^8)#unsetting 4th bit
		params.append((a,b,c))

	return params


def print_paramters(row):
	for x in row:
		print x[0],x[1],x[2]

def check_bit(num):
	if (((num>>1)&1) & ((num>>3)&1)):
		return True;
	else:
		return False;

def check_bit_unset(row):
	flag=0
	for x in row:
		if check_bit(x[2]) == True:
			print x[2]
			flag=1

	if flag == 0:
		print "No numbers found"

def delete_everything_table(conn,table_name):
	curr=conn.cursor()
	sql="TRUNCATE %s"%(table_name)
	try:
		curr.execute(sql)
		conn.commit()
		print "data deleted sucessfully"
	except:
		conn.rollback()
		print 'data not deleted'


def insert_into_table(conn,table_name):
	params=generate_parameters()
	t_sql="INSERT INTO %s (a, b, c) "%(table_name)
	sql=t_sql+"VALUES (%s, %s, %s)"
	curr=conn.cursor()
	try:
		curr.executemany(sql,params)
		conn.commit()
		print "inserted_sucessfully"
	except:
		conn.rollback()
		print "data not inserted"	
		
def insert_param_into_table(conn,table_name,rows):
	conn=connect()
	#rows=fetch_a_b_c_from_table(conn,'data')
	#rows=fetch_everything_from_table(conn,'data')
	#for x in rows:
		#print x[0],x[1],x[2],'\n'
	table_name=str(table_name)
	t_sql="INSERT INTO %s (a, b, c) "%(table_name)
	sql=t_sql+"VALUES (%s, %s, %s)"
	curr=conn.cursor()
	try:
		curr.executemany(sql,rows)
		conn.commit()
		print "inserted_sucessfully"
	except:
		conn.rollback()
		print "data not inserted"

def print_everything_from_table(conn,table_name):
	cursor=conn.cursor()
	cursor.execute("SELECT * FROM %s"%(table_name))
	results = cursor.fetchall()
	for row in results :
		print "ID = ",row[0]
		print "a = ",row[1]
		print "b = ",row[2]
		print "c = ",row[3],"\n"

def fetch_everything_from_table(conn,table_name):
	curr=conn.cursor()
	curr.execute("SELECT * FROM %s"%(table_name))
	rows=curr.fetchall()
	return rows

def create_table(conn,table_name):
	curr=conn.cursor()
	sql='''
	CREATE TABLE %s(
	ID int NOT NULL AUTO_INCREMENT,
	a int NOT NULL,
	b int NOT NULL,
	c int NOT NULL,
	PRIMARY KEY(ID))
	'''%(table_name)

	try:
		curr.execute(sql)
		conn.commit()
		print "table created"
	except:
		conn.rollback()
		print "table not created"


def fetch_everything_from_table(conn,table_name):
	curr=conn.cursor()
	curr.execute("SELECT * FROM %s"%(table_name))
	rows=curr.fetchall()
	return rows

def fetch_a_b_c_from_table(conn,table_name):
	curr=conn.cursor()
	curr.execute("SELECT a,b,c FROM %s"%(table_name))
	rows=curr.fetchall()
	return rows

def fetch_only_a_b_c_from_table(conn,table_name,id):
	curr=conn.cursor()
	try:
		curr.execute("SELECT a,b,c FROM %s WHERE ID = %d"%(table_name,id))
		row=curr.fetchone()
	except:
		print "Search not sucessfull"	
	return row

def update_only_a_b_c_in_table(conn,table_name,id,a,b,c):
	curr=conn.cursor()
	table_name=str(table_name)
	id=int(id)
	a=int(a)
	b=int(b)
	c=int(c)
	try:
		curr.execute("UPDATE %s SET a = %d,b = %d,c = %d WHERE ID = %d"%(table_name,a,b,c,id))
		conn.commit()
	except:
		conn.rollback()	

def update_all_a_b_c_in_table(conn,table_name,params):
	curr=conn.cursor()
	table_name=str(table_name)
	sql="UPDATE %s SET "%(table_name)
	sql=sql + "a = %s,b =%s,c = %s WHERE ID = %s"
	curr.executemany(sql,params)
	conn.commit()
	print "Updated sucessfully"

def connect():
	conn=mysql.connect('localhost','khoiwalrahul','buddyRahul@123','test')
	return conn


def close(conn):
	conn.close()

# Main definition - constants
menu_actions  = {}  
 
# =======================
#     MENUS FUNCTIONS
# =======================
 
# Main menu
def main_menu():
    os.system('clear')
    
    print "Welcome,\n"
    print "Please choose the following you want to start:"
    print "1. Refreshing/Deleting table_2"
    print "2. Watermarking table_2"
    print "3. Comparing original and watermarked table"
    print "4. Extracting watermark"
    print "\n0. Quit"
    choice = raw_input(" >>  ")
    exec_menu(choice)
 
    return
 
# Execute menu
def exec_menu(choice):
    os.system('clear')
    ch = choice.lower()
    if ch == '':
        menu_actions['main_menu']()
    else:
        try:
            menu_actions[ch]()
        except KeyError:
            print "Invalid selection, please try again.\n"
            menu_actions['main_menu']()
    return

# Refreshing the table
def menu1():
    copy_data_from_src_to_dest('data','data2')
    print "9. Back"
    print "0. Quit"
    choice = raw_input(" >>  ")
    exec_menu(choice)
    return

# Refreshing the table
def menu2():
    watermark('data2')
    print "9. Back"
    print "0. Quit"
    choice = raw_input(" >>  ")
    exec_menu(choice)
    return

def menu3():
    compare_tables('data','data2')
    print "9. Back"
    print "0. Quit"
    choice = raw_input(" >>  ")
    exec_menu(choice)
    return

def menu4():
    reverse_watermark('data2')
    print "9. Back"
    print "0. Quit"
    choice = raw_input(" >>  ")
    exec_menu(choice)
    return    

# Back to main menu
def back():
    menu_actions['main_menu']()
 
# Exit program
def exit():
    sys.exit()
 
# =======================
#    MENUS DEFINITIONS
# =======================
 
# Menu definition
menu_actions = {
    'main_menu': main_menu,
    '1': menu1,
    '2': menu2,
    '3': menu3,
    '4': menu4,
    '9': back,
    '0': exit,
}
 
# =======================
#      MAIN PROGRAM
# =======================
 
# Main Program
if __name__ == '__main__':
    # Launch main menu
    main_menu()