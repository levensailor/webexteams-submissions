# webexteams-submissions

A Webex Teams bot that polls for new messages, then uploads any attachments to Dropbox.

If `send_link_to_space` is `True`, a link is created and sent to a specified space along with the submitter's name. 



#### Instructions

1. Create Webex Teams bot at https://developer.webex.com/my-apps/new/bot
2. Copy API token to `token` in main.py
3. Create a Dropbox app at https://www.dropbox.com/developers/apps/create
4. Generate a token and copy to `dbx_token` in main.py
5. Run `find_roomId()` and choose the `id` of the target space for submissions as `roomId` (optional)
5. Run `pip install -r requirements.txt`
6. Run `python main.py`

#### Author Notes

This bot was built as a way for people to submit entries in a contest to be judged in a private space. 
The same could go for submitting homework assignments to a teacher, while keeping work private between students. 

Dropbox integration was only added as a workaround for the 100mb limitation in Teams API, however using Dropbox as a mirror repository for Teams files could be a great use case. 