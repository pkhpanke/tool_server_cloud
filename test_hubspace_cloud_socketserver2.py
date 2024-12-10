import http.client

import json

def test_http_server(host, port, path, data, headers):
    json_data = json.dumps(data)
    # Create a connection
    connection = http.client.HTTPConnection(host, port)

    # Send a GET request
    connection.request("POST", path, body=json_data, headers=headers)

    # Get the response
    response = connection.getresponse()
    print(f"Status: {response.status}, Reason: {response.reason}")

    # Read and print the contents of the response
    data = response.read()
    print(data.decode("utf-8"))

    # Close the connection
    connection.close()

if __name__ == "__main__":
    HOST, PORT = "43.134.112.182", 12345
    path = "/login"
    headers = {
        "Content-type": "application/json",  # Specify the content type of the payload
    }
    data = {'username': '''testDate: 2023-09-13T22:08:47
Stars: 1
Title: Garbage quality light
Content: These lights are below builder grade. Installed in my home instead of a name brand like Phillips and almost half of them have already stopped working! I now have to buy all new lights not even 4 months later and hire an electrician again!
Reviewer: Jeff

Date: 2023-06-03T14:22:36
Stars: 5
Title: Easy to Install and a Lot of Fun
Content: Cutting holes - a pain.  Installing lights - easy.  In Sure wire connectors - bonus.  Adding and naming each light in the Hubspace app was straightforward; just scan each QR code.  Linked to Alexa.  Now I can have fun creating groups and routines (see image for Christmas Kitchen routine which also plays a Christmas playlist).  Being able to change colors and brightness is a winner.  There are colors that help with waking up and relaxing.  Looking for other places to install these!!
Reviewer: TJ64

Date: 2023-04-24T03:36:22
Stars: 5
Title: Super slim and EASY
Content: I bought this to install in the place where I removed an ugly chandelier. Once I took that out I saw the 2x4 running down the middle of the hole. Contractor said this light won't work - there isn't enough clearance. As a woman, I needed to prove him wrong. I measured, 

needed .6 inch clearance, removed the existing plastic junction box and the rest was just basic wiring in the light's own junction box. Not an electrician, but can use a ladder, screwdriver and wire cutters. Great product and size
Reviewer: GirlPower

Date: 2023-04-03T04:10:53
Stars: 5
Title: Great product!
Content: Easy to install. Added to all bedrooms in our house.
Reviewer: Dialed

Date: 2023-03-29T16:23:43
Stars: 5
Title: Awesome product...
Content: Awesome product
Reviewer: Jorge

Date: 2022-12-14T17:44:05
Stars: 5
Title: Love the sleek look
Content: Modern can lights with adaptable hues. Looks very sleek.
Reviewer: Anna0927

Date: 2022-04-07T16:51:36
Stars: 5
Title: I love these lights but...
Content: I love these lights. I use the Hubspace app to set up the rooms and Alexa to control them. Just think about how to name the lights individually because Alexa will get confused if you don't speak clearly. Example-  bedroom lights is too long so just shorten it to bedroom, just make sure your Roomba isn't in the same room according to Alexa or it'll start cleaning when you turn on the bedroom, so be mindful of that. The but is make sure your wiring is not overloaded. the lights time out they're so sensitive and I had 3 blow out (the boxes) in 5 months and u can't get the J box separate, I have to get a whole new light or take it back. My HD store is cool about that. The colour ranges, what more can you ask? Purple bathroom lighting while taking a bubble bath? Yes please. These lights dim but you gotta set it to like 1% to get that incandescent type of dimming or set a routine where some lights are off and some are dim to get the effect you want, a lot of tweaking but set it and forget it. Plan your layout properly. these lights aren't floods so the standing wave phenomenon is real if you put them too close together or too far apart. Study the guide. other than that, I wish they made gimbal type full coloured lights. I'm happy with them. sorry for the long winded review
Reviewer: MrCead

Date: 2021-10-12T13:24:51
Stars: 5
Title: Best decision I made
Content: I bought 10 of these whenever refinished my basement. I love them. I don’t use the colors terribly often, but they do get used occasionally and it definitely adds something to whatever is going on.
Reviewer: TheRef

Date: 2021-09-15T15:01:02
Stars: 5
Title: Looks Great On and Off and Easy to Install
Content: Wanted a replacement light for our hallway that would look more modern.  Also though it would be helpful if that light could be turned on and off as well as be dimmed during certain parts of the day or night.



Since the hall had an existing light attached to a 4 inch box, that box had to be removed, fortunately it was attached to the drywall and not attached to the rafters.  Once the box was removed I had to enlarge the hole which involved cutting both through the drywall and a plywood backer that re-enforced the j-box. The template resulted in a perfectly sized hole and all that was left to do was to attach the metal box, which included easy connects so no wire nuts were needed.  Place the metal box and wiring into the hole and the light clips into the hole very easily.



As for connecting the light to Wi-Fi, that part I had a bit more difficulty with, but that’s because I misplaced the card with the QR code.  I tried to connect it manually, but the instructions did not warn you to make sure your Bluetooth is on and you are on your routers 2.4GHz channel.  I pulled the light back out of the ceiling (which was easy) and scanned the QR code.  Once I changed over to the 2.4 GHz channel it connected easily.  I also configure it with Alexa and was pleasantly surprised that you can voice command, on/off, dim percentage, AND basic colors with Alexa.  You can also use Alexa routines to change colors and dim, and ramp brightness up and down.  From the app you can select any custom color.  



Since this light is outside our kids bedrooms I have it set to go to 100% about an hour before bedtime, and then after bed time it ramps from 100% to 15% over 30 minutes and then stays at 15% all night.  About an hour before they wakeup it ramps from 15% to 100% over 30 minutes.  After their morning routine is done it goes to 25% for the rest of the day.  



Overall I’m quite happy with this light, it looks great.  Is plenty bright in white mode in any of the temperature colors (Goes from very warm to very cool white light).  And the RGB colors are just a fun bonus for my kids.
Reviewer: northwindone

Date: 2021-09-08T05:02:16
Stars: 4
Title: Smart multi-color slim light - so cool
Content: So we got this light because our hallway only had one light by our feet, we could never see in our hall closets. We loved the idea of a smart light, and we needed an ultra slim light,  as our A/C vent runs down the hallway, so there is no space for lights,  I wasn't even sure if this would fit... BUT IT DID!!

I am so happy to finally be able to see down my hallway,  and in my closets!!

Really easy to install.  Has push in connections for ease of wiring. 

Has so many cool features,  different light colors,  blue, aqua, red, yellow, etc. Which is just fun!

The only reason I am deducting a star, is because the HubSpace app keeps saying it is not online, which is frustrating for a smart light. 

I still love the light, I would like the app to work better.  Once the kinks in the app are worked out, it will be upgraded to 5 stars.
Reviewer: LAURIE

Date: 2021-09-03T22:27:22
Stars: 5
Title: Smart LED Downlight, no need for a hub!
Content: If you're looking for a 4" diameter downlight that can be installed w./o your typical can in the ceiling, this might be something to consider.

You can use this light w/o the smart features simply by connecting it to a circuit controlled by a light switch.  When it's not used in the smart mode, the color temperature of the light defaults to 3000K, and you cannot use the dimming features even with a dimmer switch.

As a smart light, you can remotely control the features with Alexa or Google Assistant or with the Hubspace app on your smartphone.  You can wire any number of these together on the same circuit (each unit requires 9-watts of power).

You can select either red, blue, or green instead of white.  WIth white, you can select 2200K to 6500K.  The lights are fully dimmable too with the app or with the voice control.

To utilize the features on your smartphone, you must download the free app, Hubspace and go from there.

Do save the card(s) with the QR code to simplify connections to a smartphone.  Each light fixture is uniquely identified in order to allow for individual programming.

The light fixtures do not require a ceiling can.  They come complete with a junction box that includes quick-connect lead for your feed, neutral, and ground.  

The lights are good for damp areas and also fine with contact with insulation in the ceilings.

Follow electrical code requirements when it comes to using proper couplings in the knockouts on the junction box.  You do not want to have wires going in and out of the junction box w/o their being secured in a coupling that fits the knockouts.
Reviewer: JAMES
''', 'password': '1234','filename':'testing.txt', 'file_content':'hello,world'}
# The data you want to send
    test_http_server(HOST, PORT,path, data, headers )
