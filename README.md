<p align="center">
  <img src="https://github.com/JesseHoekema/BubbleCloud/blob/main/static/logo_text_big.png?raw=true" alt="Project Logo" width="200"/>
</p>
<p align="center">
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/JesseHoekema/BubbleCloud?color=56BEB8">

  <img alt="Github language count" src="https://img.shields.io/github/languages/count/JesseHoekema/BubbleCloud?color=56BEB8">

  <img alt="Repository size" src="https://img.shields.io/github/repo-size/JesseHoekema/BubbleCloud?color=56BEB8">

  <img alt="License" src="https://img.shields.io/github/license/JesseHoekema/BubbleCloud?color=56BEB8">

  <!-- <img alt="Github issues" src="https://img.shields.io/github/issues/{{YOUR_GITHUB_USERNAME}}/bubblecloud-new?color=56BEB8" /> -->

  <!-- <img alt="Github forks" src="https://img.shields.io/github/forks/{{YOUR_GITHUB_USERNAME}}/bubblecloud-new?color=56BEB8" /> -->

  <!-- <img alt="Github stars" src="https://img.shields.io/github/stars/{{YOUR_GITHUB_USERNAME}}/bubblecloud-new?color=56BEB8" /> -->
</p>
<p align="center">
  A lightweight, self-hosted file storage solution powered by Docker.<br>
</p>
<p align="center">
  <a href="#about">About</a> &#xa0; | &#xa0; 
  <a href="#features">Features</a> &#xa0; | &#xa0;
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#installation">Installation</a> &#xa0; | &#xa0;
  <a href="https://github.com/JesseHoekema" target="_blank">Author</a>
</p>

---

##  About

A simple file storage app that runs with Docker. You can save, organize, and manage your files quickly using a clean and modern web interface. It’s easy to set up and use, so you can focus on your files instead of worrying about complicated tools.

---

##  Features
-  Fast and lightweight
-  File upload & management
-  Secure authentication
-  Modern Design
-  Super easy to set up
-  Supports file sharing to multiple platforms like discord

---
## Technologies 
The following tools were used in this project:

- [Python](https://python.org/)
- [Flask](https://flask.palletsprojects.com/)
- [Jinja2](https://jinja.palletsprojects.com/)
- [Html](https://html.com)
- [CSS](https://www.w3schools.com/css/)
- [JavaScript](https://javascript.com)
- [JSON](https://json.org)

---

## Requirements
Before starting with the **docker version**, you need to have [Docker](https://docker.com) installed.

Before starting with the **local version**, you need to have [Python](https://python.org) installed
## Installation

1. Clone the project

```bash 
git clone https://github.com/JesseHoekema/BubbleCloud
```
2. Cd into the project directory
```bash
cd BubbleCloud
```
3. Run Docker Compose Command (make sure docker is running)
```bash
docker compose up --build -d
```

4. Now the webUI is running on port: `5923` (Unless you changed it)

---

## Optional Things

1. Changing the webUI port

Open the docker-compose and edit the ports, then open the Dockerfile and edit the gunicorn command to match your port

2. Syncing the files with a directory outside of the docker container

Open the docker-compose.yml file and remove the #'s:

With #'s:
```yml
# volumes:
#  - ./YOUR_DIR_OUTSIDE_OF_CONTAINER:/app/app-files/files
```

Without #'s:
```yml
volumes:
  - ./YOUR_DIR_OUTSIDE_OF_CONTAINER:/app/app-files/files
```

After that replace the: `YOUR_DIR_OUTSIDE_OF_CONTAINER` With your directory path in your server

3. To run local run: `./local.sh` for **Mac** and `./local.bat` for **Windows**
