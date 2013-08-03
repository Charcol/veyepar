#!/usr/bin/python

# email_url.py
# emails the video URL to the presenters

from django.core.mail import get_connection, EmailMessage

from django.template import Context, Template

from process import process
from django.conf import settings

class email_title(process):

    ready_state = None

    def process_ep(self, ep):

        emails = ep.emails or ep.show.client.contacts

        if emails: 
            tos = emails.split(',')
            subject = Template("{{ep.show.name}}: Video metadata for your talk {{ep.name}}").render(Context({'ep':ep}))
            png_url = "http://veyepar.nextdayvideo.com/static/%s/%s/titles/%s.png" % ( ep.show.client.slug, ep.show.slug, ep.slug )
            body = Template( """
Hi,

This is Veyepar, the automated video processing system.

Please review the following meta data about your talk so that mistakes can be corrected now and not after the video has gone live.

Released: {{ep.released}}

* "True" means you have given us permission to record your talk and post it online.
{% if not ep.location.active %}However, we are not planning on recording any of the talks in {{ ep.location.name }}.
 {% endif %}
* "None" means it may get recorded and processed, but it will not be made public.
* "False" means you have requested not to be recorded, however the data is available for review in case you change your mind.

The video will be titled with the following image:
{{png_url}}

And the main page for the video will be here:
{{ep.public_url}}

Problems with the text will need to be fixed in the conference database that drives this page:
{{ep.conf_url}}
Except for odd word wrap on the title image.  If it bothers you, let us know how you would like it and we will try to accommodate. 

If everything looks good, you don't need to do anything. Good luck with your talk, expect another email when the video is posted.

Your talk is scheduled for {{ep.start}} in the room called {{ep.location.name}}. The conference organizers will give you instructions on where to check in before your talk.  

Email generated by https://github.com/CarlFK/veyepar/blob/master/dj/scripts/email_title.py
but replies go to a real person.

Reference: {{ep.slug}}
http://veyepar.nextdayvideo.com:8080/main/E/{{ep.id}}/
""").render(Context({ 'ep':ep, 'png_url':png_url, }) )

            # sender = 'Carl Karsten <carl@nextdayvideo.com>'
            sender = ','.join(
                    [settings.EMAIL_SENDER, ep.show.client.contacts] )
            headers = {
                # 'Reply-To': "ChiPy <chicago@python.org>"
                # 'From': sender,
                }    

            if self.options.test:
                print "tos:", tos
                print "subject:", subject
                print "body:", body
                ret = False
            else:

                connection = get_connection()
                email = EmailMessage(subject, body, sender, tos, headers=headers ) 
                ret = connection.send_messages([email])
                print tos, ret
                ret = True # need to figure out what .send_messages returns

        else:
            ret = False

        return ret

if __name__ == '__main__':
    p=email_title()
    p.main()

