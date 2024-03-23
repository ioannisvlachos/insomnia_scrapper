import bs4
import requests
import json
import re
import pprint
import os
import time
import requests
import webbrowser
import sys
import argparse
import random
from art import *
from datetime import datetime
from tqdm import tqdm


LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'
term_size = os.get_terminal_size()

def play_intro():
	print(text2art('insomniascrapper', font='doom'))
	print('Simple script to download users and comments from the high-tech forum in Greece, www.insomnia.gr.\nThe script downloads the insomnia\'s sitemap, that contains info concerning each thread!\nFollowing, it creates a version control file, that contains info, such as URL, last comment timestamp, etc, which is saved by the end of the script in order to be used for future scraping update.\nFinally, it downloads all comments from threads and stores them under path ~/output/ in json format.\nFirst database download could last days.\n')

def get_sitemap():
	play_intro()
	# search insomnia sitemap for content_forums urls using simple regex
	sm_ls = []
	urls = []
	hp_dict = {}
	urls_dict = {}
	bar_width = 100
	print('°' * term_size.columns)
	print('Getting sitemap:')
	sm = requests.get('https://www.insomnia.gr/sitemap.php')
	for item in sm.text.split('</sitemap>'):
		re_loc = re.search('(?<=<loc>).*(?=</loc>)', item)
		if re_loc:
			re_forum_con = re.search('sitemap_content_forums_Topic_', re_loc.group())
			if re_forum_con:
				sm_ls.append(re_loc.group())
	for i in range(len(sm_ls)):

		# print('Getting sitemap:\t' + sm_ls[i], end = '\r')
		url = requests.get(sm_ls[i])
		for line in url.text.split('/url'):
			re_loc = re.search('(?<=<loc>).*(?=</loc>)', line)
			re_last_modf = re.search('(?<=<lastmod>).*(?=</lastmod>)', line)
			if re_loc and re_last_modf:
				re_url_id = re.search('(?<=\/topic\/)\d+(?=\-)',re_loc.group())
				urls.append({re_url_id.group():{'url':re_loc.group(),'last_modf':re_last_modf.group(), 'last_page_updated':1}})
		percentage = (i / len(sm_ls)) * 100
		progress = int(bar_width * (i / len(sm_ls)))
		bar = "[" + "|" * progress + " " * (bar_width - progress) + "]"
		print(f"{sm_ls[i]}\t\tProgress: {percentage:.2f}% {bar}")
		print(LINE_UP, end=LINE_CLEAR)
		# print(f"\t\tProgress: {percentage:.2f}% {bar}", end = '\r')
	print('°' * term_size.columns)
	print('Getting comments..')
	return urls


def get_comments_from_thread(thread_id, ver_control, index_ver_control, loop_state, pool_len, save_folder):
	comments_ls = []
	bar_width = 20
	if os.path.isfile(os.getcwd() + '/' + save_folder + '/' + 'thread_id' + '.json'):
		file = open(thread_id + '.json')
		js = json.loads(file.read())
		for item in js:
			comments_ls.append(*item.keys())
	else:
		js = []

	url = ver_control[index_ver_control[thread_id]][thread_id]['url']
	try:
		last_page_updated = ver_control[index_ver_control[thread_id]][thread_id]['last_page_updated']	
	except Exception:
		last_page_updated = 1	

	r = requests.get(url, timeout=100)
	html = bs4.BeautifulSoup(r.text, 'html.parser')  
	if html.title.text == 'Συγνώμη, δεν μπορέσαμε να εντοπίσουμε ατό που ζητήσατε!':
		print('[-] thread {} is offline'.format(thread_id))
		js.append({thread_id:{'comments':[]}})
		with open(os.getcwd() + '/' + save_folder + '/' + thread_id + '.json', 'w') as export:
			data = json.dumps(js, ensure_ascii = False, indent = 4)
			export.write(data) 
	else:
		d = json.loads(html.find('script', type='application/ld+json').text)
		if d['@type'] == 'DiscussionForumPosting':
			if last_page_updated > 1:
				pageStart = last_page_updated
			else:
				pageStart = d['pageStart']
			pageEnd = d['pageEnd'] + 1
			thread_url = d['url']
			dateCreated = d['dateCreated']
			question = d['text']
			if 'url' in d['author'].keys():
				author_id = re.search('(?<=\/profile\/)\d+(?=\-)', d['author']['url'])
				ts = author_id.group()
			else:
				ts = '0'
			if len(js) == 0:
				js.append({'title_' + thread_id:{'commenter_id':ts, 'comment_date':dateCreated, 'comment_body':question}})
			for i in range(pageStart, pageEnd):
				# print('[+] Downloading comment page {}/{} from thread {}'.format(i,pageEnd -1,thread_id))
				r = requests.get(url + '/page/' + str(i))
				html = bs4.BeautifulSoup(r.text, 'html.parser')  
				d = json.loads(html.find('script', type='application/ld+json').text)
				if 'comment' not in d.keys():
					continue
				for comment in d['comment']:
					# print(comment)
					comment_id = re.search('(?<=#comment-)\d+', comment['url'])
					if comment_id in comments_ls:
						continue
					else:
						if 'url' in comment['author']:
							commenter_id = re.search('(?<=\/profile\/)\d+(?=\-)', comment['author']['url'])
						else:
							commenter_id = re.search('(?<=\/profile\/)\d+(?=\-)','https://www.insomnia.gr/profile/0-visitor')
						# commenter_id = re.search('(?<=\/profile\/)\d+(?=\-)', comment['author']['url'])
						comment_body = ' '.join(comment['text'].split())
						comment_date = comment['dateCreated']
						js.append({comment_id.group():{'commenter_id':commenter_id.group(), 'comment_date':comment_date, 'comment_body':comment_body}})
				percentage_current = (i / (pageEnd-1)) * 100
				progress_current = int(bar_width * (i / (pageEnd-1)))
				bar_current = "[" + "=" * progress_current + " " * (bar_width - progress_current) + "]"
				# print(f"\t\t{percentage_current:.2f}% {bar_current}", end = '')

				percentage_all = (loop_state / pool_len) * 100
				progress_all = int(bar_width * (loop_state / pool_len))
				bar_all = "[" + "=" * progress_all + " " * (bar_width - progress_all) + "]"
				# print(f"\t\t{percentage_all:.2f}% {bar_all}")
				print(f'[+] Downloading comment page {i}/{pageEnd -1} from thread {thread_id}\t\tcurrent_thread_progress: {percentage_current:.2f}% {bar_current}\t\tProgress: {percentage_all:.2f}% {bar_all}')
				print(LINE_UP, end=LINE_CLEAR)
			ver_control[index_ver_control[thread_id]][thread_id]['last_page_updated'] = d['pageEnd']
			with open(os.getcwd() + '/' + save_folder + '/' + thread_id + '.json', 'w') as export:
				data = json.dumps(js, ensure_ascii = False, indent = 4)
				export.write(data)
		if d['@type'] == 'QAPage':
			thread_url = d['url']
			dateCreated = d['dateCreated']
			if url in d['author'].keys():
				author_id = re.search('(?<=\/profile\/)\d+(?=\-)', d['author']['url'])
			else:
				author_id = re.search('(?<=\/profile\/)\d+(?=\-)', 'https://www.insomnia.gr/profile/0-visitor')
			if 'acceptedAnswer' in d['mainEntity'].keys():
				comment_id = re.search('(?<=findComment&comment=)\d+', d['mainEntity']['acceptedAnswer']['url'])
				if 'url' in d['mainEntity']['acceptedAnswer']['author']:
					commenter_id = re.search('(?<=\/profile\/)\d+(?=\-)', d['mainEntity']['acceptedAnswer']['author']['url'])
				else:
					commenter_id = re.search('(?<=\/profile\/)\d+(?=\-)','https://www.insomnia.gr/profile/0-visitor')	
				comment_body = ' '.join(d['mainEntity']['acceptedAnswer']['text'].split())
				comment_date = d['mainEntity']['acceptedAnswer']['dateCreated']
				js.append({comment_id.group():{'commenter_id':commenter_id.group(), 'comment_date':comment_date, 'comment_body':comment_body}})
			if len(d['mainEntity']['suggestedAnswer'])> 0:
				print('[+] Downloading all suggestedAnswers (len {}) from Q/A thread {}'.format(len(d['mainEntity']['suggestedAnswer']),thread_id))
				print(LINE_UP, end=LINE_CLEAR)
				for item in d['mainEntity']['suggestedAnswer']:
					comment_id = re.search('(?<=#comment-)\d+', item['url'])
					if 'url' in item['author']:
						commenter_id = re.search('(?<=\/profile\/)\d+(?=\-)', item['author']['url'])
					else:
						commenter_id = re.search('(?<=\/profile\/)\d+(?=\-)','https://www.insomnia.gr/profile/0-visitor')	
					comment_body = ' '.join(item['text'].split())
					comment_date = item['dateCreated']	
					js.append({comment_id.group():{'commenter_id':commenter_id.group(), 'comment_date':comment_date, 'comment_body':comment_body}})
			with open(os.getcwd() + '/' + save_folder + '/' + thread_id + '.json', 'w') as export:
				data = json.dumps(js, ensure_ascii = False, indent = 4)
				export.write(data) 	
		# comments_dict.update({url_id:{'url':url, 'last_modf':last_modf, 'comments':page_list}})



def create_db_folder():
	if not os.path.isdir('output'):
		os.mkdir('output')

def create_sample_folder():
	if not os.path.isdir('sample'):
		os.mkdir('sample')

def create_user_folder():
	if not os.path.isdir('users'):
		os.mkdir('users')

		 
def get_download_pool(forum_url_old, forum_url_new):
	dates_old = []
	dates_new = []	
	threads_to_be_updated = []
	hp_list = []
	pos_old = {}

	# check if script's first run
	if forum_url_old == []:
		for item in forum_url_new:
			for key in item.keys():
				threads_to_be_updated.append(key)
		return threads_to_be_updated
	else:			
		# transform dicts into strings for faster parsing
		for threads in forum_url_new:
			for key in threads.keys():
				dates_new.append(key+'*'+threads[key]['last_modf'])

		for threads in forum_url_old:
			for key in threads.keys():
				dates_old.append(key+'*'+threads[key]['last_modf'])


		# compare lists
		diff = list(set(dates_new) - set(dates_old))
		for item in diff:
			spl_item = item.split('*')
			threads_to_be_updated.append(spl_item[0])

		index_ver_control_old = return_index_ver_control(forum_url_old)
		index_ver_control_new = return_index_ver_control(forum_url_new)


		# updating last_page value
		for item in forum_url_new:
			for key in item.keys():
				if key in threads_to_be_updated and key in index_ver_control_old.keys():
					item[key]['last_page_updated'] = forum_url_old[index_ver_control_old[key]][key]['last_page_updated']
				else:
					item[key]['last_page_updated'] = 1

		# fixing sitemap bug
		for key in index_ver_control_old.keys():
			if key not in index_ver_control_new.keys():
				forum_url_new.append(forum_url_old[index_ver_control_old[key]])

		return threads_to_be_updated



def return_index_ver_control(ver_control):
	index_ver_control = {}
	for index in range(len(ver_control)):
		for key in ver_control[index].keys():
			index_ver_control.update({key:index})
	return index_ver_control


def get_latest_user():
	print('[-] Now opening browser, locate latest_user_id...')
	webbrowser.open('https://www.insomnia.gr/search/?type=core_members&joinedDate=any&group[17]=1&group[18]=1&group[4]=1&group[21]=1&group[23]=1&group[3]=1&group[19]=1&group[15]=1&group[6]=1&group[13]=1&group[20]=1&group[16]=1&group[7]=1&sortby=joined&sortdirection=desc')
	latest_user = input('[+] Insert latest_user_id: ')
	return latest_user

def get_user():
	js = {}
	search_list = []
	output = []
	birthday = ''
	last_user_in_db = 0

	create_user_folder()

	if not os.path.isfile(os.getcwd() + '/users/insomnia_mem.json'):
		all_users = open(os.getcwd() +'/users/insomnia_mem.json', 'w')
		all_users.close()

	if os.path.isfile(os.getcwd() + '/users/insomnia_mem.json'):
		f = open(os.getcwd() + '/users/insomnia_mem.json','r',encoding = 'utf8')
		user_db = json.loads(f.read())
		for item in user_db:
			for key in item.keys():
				if key == '0':
					last_user_in_db = item[key]

	# create/load error log
	if not os.path.isfile('user_log.txt'):
		error_log = open('user_log.txt', 'w')

	latest_user = get_latest_user()
	for uuid in range(last_user_in_db, int(latest_user)):
		try:
			r = requests.get('https://www.insomnia.gr/?app=core&module=members&controller=profile&id=' + str(uuid))
			html = bs4.BeautifulSoup(r.text, 'html.parser')
			try:
				d = json.loads(html.find('script', type='application/ld+json').text)
			except Exception:
				print('[-] UserId: ' + str(uuid) + ' | NOT_FOUND')
				continue
					
			username = d['name']
			url = d['url']
			reg_date = d['dateCreated']
			num_messages = d['interactionStatistic'][0]['userInteractionCount']
			profile_views = d['interactionStatistic'][1]['userInteractionCount']
			is_active = 1
			print('[-] Requesting userId: ' + str(uuid) + '| username: ' + username)

			if html.title.text == 'Συγνώμη, δεν μπορέσαμε να εντοπίσουμε ατό που ζητήσατε!' or html.title.text == 'Συγνώμη, δεν έχετε πρόσβαση!':
				is_active = 0
				js.update({uuid:{'username':username, 'url': url, 'reg_date': reg_date, 'profile_views': profile_views, 'num_messages': num_messages, 'is_active': is_active}})
				output.append(js)
				js = {}
				continue

			# get last_seen date
			reg_last_seen = re.search('Ποτέ', html.text)
			if reg_last_seen:
				last_seen = '1900/01/01'
			else:
				js_list = html.find_all('time')
				if js_list != '':
					for item in js_list:
						search_list.append(item.get('datetime'))
					if len(search_list) == 0:
						last_seen = '1900/01/01'
					if len(search_list) == 1:
						last_seen = search_list[0]
					if len(search_list) > 1:
						last_seen = search_list[1]		
					search_list = []

			# get birthday
			js_list = html.find_all('span')
			if js_list != '':
				for item in js_list:
					if type(item.get('class')) is list and item.get('class')[0] == 'ipsList_reset':
						search_list.append(item.text)
				if len(search_list)>0:
					birthday = search_list[0]
				search_list = []

			if birthday != '':
				js.update({uuid:{'username':username, 'url': url, 'birthday':birthday, 'reg_date': reg_date, 'last_seen': last_seen, 'profile_views': profile_views, 'num_messages': num_messages, 'is_active': is_active}})
				birthday = ''
			else:
				js.update({uuid:{'username':username, 'url': url, 'reg_date': reg_date, 'last_seen': last_seen, 'profile_views': profile_views, 'num_messages': num_messages, 'is_active': is_active}})
			
				
			output.append(js)
			js = {}
		except Exception:
			with open('user_log.txt', 'a') as error:
				error.write('[-] Error in userid ' + tr(uuid))
				error.write('\n')
			continue
	# update latest_user_in_db		
	js.update({'0':int(latest_user)})

	with open(os.getcwd() + '/users/insomnia_mem.json','a') as export:
		data = json.dumps(output, ensure_ascii = False, indent = 4)
		export.write(data)

def get_sample_pool(pool):
	hp_list = []
	for i in range(100):
		hp_list.append(pool[random.randint(0, len(pool))])
	return hp_list	


def download_pool(pool, ver_control, start_time, save_folder):
	error_ind = 0
	index_ver_control = return_index_ver_control(ver_control)
	for i in range(len(pool)):
		try:
			get_comments_from_thread(pool[i], ver_control, index_ver_control, i, len(pool), save_folder)
		except Exception as e:
			if error_ind == 0:
				error = '[*] Programm started successfully in {}'.format(start_time)
				error_ind = -1
			if not os.path.isfile('error_log.txt'):
				with open('error_log.txt', 'w') as error_log:
					error_log.write(error)
			else:
				with open('error_log.txt', 'a') as error_log:
					error = '- Error in thread {}\tTimestamp: {}\tErrorMessage: {}'.format(pool[i], datetime.now().isoformat(timespec='milliseconds'), e)
					error_log.write(error)
					print(error)
	

def dump_ver_control(ver_control):
	with open('ver_control','w') as export:
		data = json.dumps(ver_control, ensure_ascii = False, indent = 4)
		export.write(data)		

def main():
	start_time = datetime.now().isoformat(timespec='milliseconds')
	save_folder = 'output'
	parser = argparse.ArgumentParser(description='BS4 script to scrape threads from insomnia.gr forum, for no reason! Have fun!', epilog="Thanks for using insomniascrapper!")
	parser.add_argument('-d', '--download-all', help='Downloads all insomnia.gr forum', action='store_true')  # can 'store_false' for no-xxx flags
	parser.add_argument('-u', '--update', help='Update database', action="store_true")
	parser.add_argument('-m', '--members', help='Get/update users_db', action="store_true")
	parser.add_argument('-v', '--version-control', help='Get only version control file.')
	parser.add_argument('-s', '--sample', help='Gets 100 random threads, just for testing.', action="store_true")
	parser.add_argument('-w', '--working-directory', choices=['output', 'sample'], help='Choose either database [output] or sample database [sample] to search.')
	parser.add_argument('-i', '--info', help='Return database/sample info (number of threads, total size).', action="store_true")
	parser.add_argument('-c', '--check', help='Check if thread_id.json is in database/sample.')
	parser.add_argument('-t', '--ts', help='Return ts of thread_id.')
	parsed = parser.parse_args()
	
	if parsed.members:
		get_user()

	if parsed.download_all:
		ver_control_current = []

		#check if db folder exists
		create_db_folder()

		# get sitemap
		ver_control = get_sitemap()

		# getting thread pool ready to download
		pool = get_download_pool(ver_control_current, ver_control)
		print(f'Threads to be downloaded\n{pool}')
		print(f'Number of threads in pool: {len(pool)}')

		# downloading pool
		download_pool(pool, ver_control, start_time, save_folder)

		# saving ver_control for future need
		dump_ver_control(ver_control)

	if parsed.update:
		save_folder = 'output'
		# load current ver_control
		if not os.path.isfile('ver_control'):
		    ver_control_current = []
		else:
		    forum_urls_old = open(r'ver_control')
		    ver_control_current = json.loads(forum_urls_old.read())

		#check if db folder exists
		create_db_folder()

		# get sitemap
		# ver_control = get_sitemap()
		f = open('ver_new')
		ver_control = json.loads(f.read())


		# getting thread pool ready to download
		pool = get_download_pool(ver_control_current, ver_control)
		print(f'Threads to be downloaded\n{pool}')
		print(f'Number of threads in pool: {len(pool)}')

		# downloading pool
		download_pool(pool, ver_control, start_time, save_folder)

		# saving ver_control for future need
		dump_ver_control(ver_control)

	if parsed.sample:
		save_folder = 'sample'
		ver_control_current = []

		#check if sample folder exists
		create_sample_folder()

		# get sitemap
		ver_control = get_sitemap()

		# getting thread pool 
		pool = get_download_pool(ver_control_current, ver_control)

		# getting random threads from pool
		sample_pool = get_sample_pool(pool)

		# downloading pool
		download_pool(sample_pool, ver_control, start_time, save_folder)

	if parsed.version_control:
		# get sitemap
		ver_control = get_sitemap()

		# saving ver_control for future need
		dump_ver_control(ver_control)

	if parsed.ts and parsed.working_directory:
		js_file = parsed.ts
		try:
			f = open(os.getcwd() + '/' + parsed.working_directory + '/' + js_file + '.json')
			d = json.loads(f.read())
			for key in d[0].keys():
				print(d[0][key]['comment_date'])
				print(d[0][key]['comment_body'])
		except Exception as e:
			print(e)	

	if parsed.check and parsed.working_directory:
		check_thread = 'ls -h ' + parsed.working_directory + ' | grep ' + parsed.check
		os.system(check_thread)

	if parsed.ts and parsed.working_directory is None:
		print('error: the following arguments are required: -w/--working-directory')

	if parsed.check and parsed.ts is None:
		print('error: the following arguments are required: -w/--working-directory')
		
	if parsed.info and parsed.working_directory is None:
		print('error: the following arguments are required: -w/--working-directory')
		
	if parsed.info and parsed.working_directory:
		number_threads = 'echo Number of threads: $(ls ' + parsed.working_directory + ' | wc -l)'
		size_folder = 'echo Size of folder: $(du -h '+ parsed.working_directory + '/ | grep -Po \'^[a-zA-Z0-9.]+\')'
		os.system(number_threads)
		os.system(size_folder)
		
	
if __name__ == "__main__":
    main()
