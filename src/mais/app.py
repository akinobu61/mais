
import os
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import pyshorteners
import secrets
from .url_crypto import encrypt_url, decrypt_url
from .content_processor import process_content
from .proxy_utils import get_proxy_url

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
