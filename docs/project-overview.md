# astrology-backend

## Introduction
astrology-prediction is a full-stack web application. The application consists of a back-end server and a front-end server.

## Purpose
The purpose of this application is to help users understand their future through Indian palmistry. Users will upload an image of their hand to the server via an API. The server will use openAI's 4.1-mini model to evaluate the image and give a response. The user can then briefly speak with the server via API and ask follow on questions. The server will use the openAI model to respond to follow on questions. All of these things will be rendered and shown to the user via a front-end web-app.

## Scope
The scope of the project is:
1. Create a server using python
2. Exposes various APIs using fastapi
3. The server enables server side login and authentication APIs 
4. The server has a database which logs user login passwrod, conversations etc
5. The server exposes APIs for:
    - Log In 
    - Log Out
    - Upload Image
    - Analyse Image
    - Get results of Analyses
    - Talk to model for further discussion on analyses in a conversation
    - Start a new Conversation
    - Delete a conversation
    - Fetch an old Conversation
    - Update a Conversation
6. Create a Front End web app which users can use to interact with the application
7. Users can log into the application, start a new conversation, get insights, and other features.

## Goals
The goal of the project is to:
1. Create a safe, secure, back-end server and database
2. Expose APIs for front-end to consume
3. Interface with AI to get responses and engage users in conversation
4. Create a safe, intuitive, user-friendly, and pretty front-end web-app

## Non Goals
These are the things the project is not expected to do:
- Manual Palmistry without AI
- Non-Palmistry Astrology features in V1
