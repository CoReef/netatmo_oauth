build:
	docker build -t netatmo_oauth_image .
run:
	docker run -d -p 4344:4344 -v v_coreef:/coreef --name netatmo_oauth_coreef netatmo_oauth_image
	# docker run -d --restart=unless-stopped -p 4344:4344 -v v_coreef:/coreef --name netatmo_auth_coreef netatmo_auth_image
clean:
	find . -name '__pycache__' | xargs rm -rf;
