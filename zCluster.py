

from boto.ec2.connection import EC2Connection



conn = EC2Connection('<aws access key>', '<aws secret key>')

#key_pair = conn.create_key_pair('gsg-keypair')
#print key_pair.fingerprint

#images = conn.get_all_images()
#image = images[0] #???
#reservation = image.run(key_name='gsg-keypair')

#instance = reservation.instances[0]


                    