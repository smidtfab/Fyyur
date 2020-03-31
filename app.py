#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys 

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

# connect to a local postgresql database
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# Venue model
class Venue(db.Model):
  __tablename__ = 'Venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  address = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
  website = db.Column(db.String(500))
  seeking_talent = db.Column(db.Boolean, default=True)
  seeking_description = db.Column(db.String(120))
  shows = db.relationship('Show', backref='venue', lazy=True)

  def __repr__(self):
      return f'<Venue {self.id} {self.name}>'


# Artist model
class Artist(db.Model):
  __tablename__ = 'Artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120))
  genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website = db.Column(db.String(500))
  seeking_venue = db.Column(db.Boolean, default=True)
  seeking_description = db.Column(db.String(120))
  shows = db.relationship('Show', backref='artist', lazy=True)

  def __repr__(self):
      return f'<Artist {self.id} {self.name}>'


# Show model
class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey(
      'Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False,
                        default=datetime.utcnow)

  def __repr__(self):
    return f'<Show {self.id}, Artist {self.artist_id}, Venue {self.venue_id}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # list for storing venue data
  data = []

  # get all the venues and create a set from the cities
  venues = Venue.query.all()
  print(venues)
  venue_cities = set()
  for venue in venues:
      # add city/state tuples
      venue_cities.add((venue.city, venue.state))

  # for each unique city/state, add venues
  for location in venue_cities:
      data.append({
          "city": location[0],
          "state": location[1],
          "venues": []
      })

  # get number of upcoming shows for each venue
  for venue in venues:
      num_upcoming_shows = 0

      shows = Show.query.filter_by(venue_id=venue.id).all()

      # if the show start time is after now, add to upcoming
      for show in shows:
          if show.start_time > datetime.now():
              num_upcoming_shows += 1

      # for each entry, add venues to matching city/state
      for entry in data:
          if venue.city == entry['city'] and venue.state == entry['state']:
              entry['venues'].append({
                  "id": venue.id,
                  "name": venue.name,
                  "num_upcoming_shows": num_upcoming_shows
              })

  # return venues page with data
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # search on artists with partial string search. It is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search_term = request.form.get('search_term', '')

  venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()

  venue_data = []

  for venue in venues:
    venue_data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": 0, # does not have any functionality here, but follows same procedure as seen before
    })

  response = {
    "count": len(venues),
    "data": venue_data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

def get_upcoming_shows_for_venue(shows):
  upcoming_shows = []
  for show in shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time": str(show.start_time)
      })
  return upcoming_shows

def get_past_shows_for_venue(shows):
  past_shows = []
  for show in shows:
    if show.start_time <= datetime.now():
      past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time": str(show.start_time)
      })
  return past_shows

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # get venue by id
  venue = Venue.query.get(venue_id)

  # get shows by id
  shows = Show.query.filter_by(venue_id=venue_id)

  venue_data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": get_past_shows_for_venue(shows),
    "upcoming_shows": get_upcoming_shows_for_venue(shows),
    "past_shows_count": len(get_past_shows_for_venue(shows)),
    "upcoming_shows_count": len(get_upcoming_shows_for_venue(shows))
  }

  return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    # get all attributes for venue from client request
    form = VenueForm()
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    genres = request.form['genres']
    facebook_link = request.form['facebook_link']
    website = ""
    image_link = ""
    seeking_talent = True
    seeking_description = ""

    # create venue and add it to db
    venue = Venue(name=name, city=city, state=state, address=address,
                  phone=phone, genres=genres, facebook_link=facebook_link,
                  website=website, image_link=image_link,
                  seeking_talent=seeking_talent,
                  seeking_description=seeking_description)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
    venue = Venue.query.get(venue_id) 
    db.session.delete(venue)
    db.session.commit()
    flash('Venue ' + Venue.query.get(venue_id) + ' was successfully deleted.')
  except:
    flash('An error occurred. Venue ' + Venue.query.get(venue_id) + ' could not be deleted.')
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get('search_term', '')

  artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()

  artist_data = []

  for artist in artists:
    artist_data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": 0, # does not have any functionality here, but follows same procedure as seen before
    })

  response = {
    "count": len(artists),
    "data": artist_data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

def get_upcoming_shows_for_artist(shows):
  upcoming_shows = []
  for show in shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
        'venue_id' : show.venue_id,
        'venue_name' : Venue.query.filter_by(id=show.venue_id).first().name,
        'venue_image_link': Venue.query.filter_by(id=show.venue_id).first().image_link,
        'start_time': str(show.start_time)
      })
  return upcoming_shows

def get_past_shows_for_artist(shows):
  past_shows = []
  for show in shows:
    if show.start_time <= datetime.now():
      past_shows.append({
        'venue_id' : show.venue_id,
        'venue_name' : Venue.query.filter_by(id=show.venue_id).first().name,
        'venue_image_link': Venue.query.filter_by(id=show.venue_id).first().image_link,
        'start_time': str(show.start_time)
      })
  return past_shows

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  
  # get artist by id
  artist = Artist.query.filter_by(id=artist_id).first()

  # get all shows matching artist id
  shows = Show.query.filter_by(artist_id=artist_id).all()

  artist_data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": get_past_shows_for_artist(shows),
    "upcoming_shows": get_upcoming_shows_for_artist(shows),
    "past_shows_count": len(get_past_shows_for_artist(shows)),
    "upcoming_shows_count": len(get_upcoming_shows_for_artist(shows)),
  }
  
  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  # retrieve venue
  artist = Artist.query.filter_by(id=artist_id).first()

  # set attributes
  artist={
    "id": artist_id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    form = ArtistForm()

    # get venue by id
    artist = Artist.query.filter_by(id=artist_id).first()

    # load form data from user input
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form['genres']
    artist.facebook_link = request.form['facebook_link']
    artist.website = ""
    artist.image_link = ""
    artist.seeking_venue = False
    artist.seeking_description = ""

    # commit changes, flash message if successful
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    # catch errors
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  finally:
    # close the session
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  # retrieve venue
  venue = Venue.query.filter_by(id=venue_id).first()

  # set attributes
  venue_data = {
    "id": venue_id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }

  '''
  venue = {
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  '''

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue_data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = VenueForm()

    # get venue by id
    venue = Venue.query.filter_by(id=venue_id).first()

    # load form data from user input
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form['genres']
    venue.facebook_link = request.form['facebook_link']
    venue.website = ""
    venue.image_link = ""
    venue.seeking_talent = True
    venue.seeking_description = ""

    # commit changes, flash message if successful
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    # catch errors
    db.session.rollback()
    flash('An error occurred. Venue ' +
          request.form['name'] + ' could not be updated.')
  finally:
    # close the session
    db.session.close()

  # return redirect to venue page
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  try:
    # get all attributes for venue from client request
    form = ArtistForm()
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form['genres']
    facebook_link = request.form['facebook_link']
    website = ""
    image_link = ""
    seeking_venue = False
    seeking_description = ""

    # create venue and add it to db
    artist = Artist(name=name, city=city, state=state, phone=phone,
                    genres=genres, facebook_link=facebook_link,
                    website=website, image_link=image_link,
                    seeking_venue=seeking_venue,
                    seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows

  show_data = []

  # get all shows
  shows = Show.query.all()

  # build up show json 
  for show in shows:
    show_data.append({
      "venue_id": show.venue_id,
      "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
      "artist_id": show.artist_id,
      "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
      "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
      "start_time": str(show.start_time)
    })

  return render_template('pages/shows.html', shows=show_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called upon submitting the new show listing form
  try:
    # input
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']

    # create new show with user data
    show = Show(artist_id=artist_id, venue_id=venue_id,
                start_time=start_time)

    # add show and commit session
    db.session.add(show)
    db.session.commit()

    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
