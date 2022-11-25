#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from email.policy import default
from hashlib import new
import json
from os import abort
import sys
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text)
    show = db.relationship('Show', backref='Venue', lazy=True, cascade="save-update")
    # A venue can have multiple genres
    genres = db.Column(db.ARRAY(db.String(50)))
    

class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120)) 
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.Text)

    # An artist can have multiple shows and a show can have multiple artists
    shows = db.relationship('Show', backref="Artist", lazy=True)
    # An artist can have multiple genres
    genres = db.Column(db.ARRAY(db.String(50)))

    
class Show(db.Model):
      __tablename__ = 'Show'

      id = db.Column(db.Integer, primary_key=True)
      date = db.Column(db.DateTime, nullable=False)
      venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'),nullable=False)
      artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)


      
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(str(value))
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venues = Venue.query.distinct(Venue.state, Venue.city).all()
  print (venues)
  data = []
  
  # getting all the city and states
  for venue_state_city in venues:
    city = venue_state_city.city
    state = venue_state_city.state
    venues = Venue.query.filter(Venue.city == city, Venue.state == state)
    venues_list = []
    # getting all the venues in a specific city and state
    for venue in venues:
      venues_list.append({
        'id': venue.id,
        'name': venue.name,
        # Compute the length of an array of shows with date > today's date
        'num_upcoming_shows': len([show for show in venue.show if show.date > datetime.now()])
      })
    data.append({
      'city': city,
      'state': state,
      'venues': venues_list
    })

  print(data)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search = request.form.get('search_term','')

  # ilike is for case insensitive search
  venues = Venue.query.filter(Venue.name.ilike('%{}%'.format(search))).all()
  count = len(venues)
  # Search an artist from venue page
  if count == 0:
    return search_artists() 
  else:
    data = []
    for venue in venues:
      data.append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': len([show for show in venue.show if show.date > datetime.now()])
      })
    response = {
      'count': count,
      'data': data
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  try:
    venue = Venue.query.get(venue_id)
    
    # Same list comprehension used above to compute past and upcoming shows
    past_shows = [show for show in venue.show if show.date < datetime.now()]
    upcoming_shows = [show for show in venue.show if show.date > datetime.now()]
    past_shows_count = len(past_shows)
    upcoming_shows_count = len(upcoming_shows)

    # Converting the result into a dictionary using dictionary comprehension syntax
    data = {column: str(getattr(venue, column)) for column in venue.__table__.c.keys()}

    data['genres'] = venue.genres
    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = past_shows_count
    data['upcoming_shows_count'] = upcoming_shows_count
  except:
    flash('Venue does not exist')
    return venues()

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  new_venue = Venue()
  form = VenueForm(request.form)
  if form.validate():
    form.populate_obj(new_venue)
    error = False

    try:
      db.session.add(new_venue)
      
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()

    if error:
      flash('An error occurred while listing Venue: ' + request.form['name'] + ' could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  else:
    for error in form.errors.items():
      flash(error) 
      return create_venue_form()

  return render_template('pages/home.html')



@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id = venue_id).delete()
    db.session.commit()
    flash('Venue ' + Venue.name + ' has been successfully deleted!')
  except:
    db.session.rollback()
    flash('Error while deleting Venue: ' + Venue.name)
  finally:
    db.session.close()  

  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data = []
  for artist in artists:
    data.append({
      'id': artist.id,
      'name': artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search = request.form.get('search_term','')
  # print (search)

  artists = Artist.query.filter(Artist.name.ilike('%{}%'.format(search))).all()
  count = len(artists)

  data = []
  for artist in artists:
    data.append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': len([show for show in artist.shows if show.date > datetime.now()])
    })
  response = {
    'count': count,
    'data': data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  try:
    artist = Artist.query.get(artist_id)
  
    # Same list comprehension used in the venues object
    past_shows = [show for show in artist.shows if show.date < datetime.now()]
    upcoming_shows = [show for show in artist.shows if show.date > datetime.now()]
    past_shows_count = len(past_shows)
    upcoming_shows_count = len(upcoming_shows)

    data = {column: str(getattr(artist, column)) for column in artist.__table__.c.keys()}

    data['genres'] = artist.genres
    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = past_shows_count
    data['upcoming_shows_count'] = upcoming_shows_count
  except:
    flash('Artist does not exist')
    return artists()

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  try:
    artist = Artist.query.get(artist_id)
    artist = {column: str(getattr(artist, column)) for column in artist.__table__.c.keys()}
  except:
    flash('Cannot edit non-existing artist')
    return artists()
  
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # artist record with ID <artist_id> using the new attributes
  error = False
  
  try:
      artist = Artist.query.get(artist_id)
      form = ArtistForm(request.form)
      form.populate_obj(artist)

      db.session.add(artist)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
      if error:
          flash('Could not update Artist: ' + request.form['name'])
      else:
          flash('Artist: ' + request.form['name'] +' has been successfully updated!')
  

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  try:
    venue = Venue.query.get(venue_id)
    venue = {column: str(getattr(venue, column)) for column in venue.__table__.c.keys()}
  except:
    flash('Cannot edit non-existing venue')
    return venues()

  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  error = False
  
  try:
      venue = Venue.query.get(venue_id)
      form = VenueForm(request.form)
      form.populate_obj(venue)

      db.session.add(venue)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
  finally:
      db.session.close()
      if error:
          flash('Could not update Venue: ' + request.form['name'])
      else:
          flash('Venue: ' + request.form['name'] +' has been successfully updated!')
  
  return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  new_artist = Artist()
  form = ArtistForm(request.form)
  if form.validate():
    form.populate_obj(new_artist)
    error = False

    try:
      db.session.add(new_artist)
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()

    if error:
      flash('An error occurred while listing Artist: ' + request.form['name'])
    else:
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
  else:
    for error in form.errors.items():
      flash(error) 
      return create_artist_form()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shows = Show.query.all()
  data = []
  for show in shows:
    data.append({
      'venue_id': show.Venue.id,
      'venue_name': show.Venue.name,
      'artist_id': show.Artist.id,
      'artist_name': show.Artist.name,
      'artist_image_link': show.Artist.image_link,
      'start_time': str(show.date)
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  new_show = Show()
  form = ShowForm(request.form)
  if form.validate():
    form.populate_obj(new_show)
    error = False

    try:
      db.session.add(new_show)
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()

    if error:
      flash('An error occurred while listing Show at: ' + request.form['venue_id'] + ' with artist: '+ request.form['artist_id'])
    else:
      # on successful db insert, flash success
      flash('Show at: ' + request.form['venue_id'] + ' with artist: '+ request.form['artist_id'] +' was successfully listed!')

  else:
    for error in form.errors.items():
      flash(error) 
      return create_shows() 

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
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
