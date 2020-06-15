#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKeyConstraint
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import date
import sys
import enum
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# !TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


# Child model
class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(db.ARRAY(db.String()))
    # new form addition
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(120))
    past_shows_count = db.Column(db.Integer, default=0)
    upcoming_shows_count = db.Column(db.Integer, default=0)
    # creating the relationship
    artists = db.relationship("Show", back_populates="venue")

    def __repr__(self):
        return f'<Venue Id: {self.id}, Name: {self.name}>'


# Parent
class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    venues = db.relationship('Show', back_populates='artist')
    seeking_venue = db.Column(db.Boolean, nullable=True, default=False)
    seeking_description = db.Column(
        db.String(120), default="Not currently seeking performance venues")
    website = db.Column(db.String(120))

    past_shows = db.Column(db.ARRAY(db.String(), dimensions=4))
    past_shows_count = db.Column(db.Integer, default=0)
    upcoming_shows = db.Column(db.PickleType)
    upcoming_shows_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Artist Id: {self.id}, Name: {self.name}>'

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Show(db.Model):
    __tablename__ = "Show"

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.String(120))
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'Venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), nullable=False)
    venue_name = db.Column(db.String(120))
    artist_name = db.Column(db.String(120))
    artist_image_link = db.Column(
        db.String(500))
    # creating the relationship
    artist = db.relationship('Artist', back_populates='venues')
    venue = db.relationship('Venue', back_populates='artists')

    def __repr__(self):
        return f'<Artist Id: {self.artist_id}, Venue Id: {self.venue_id}, Start Time: {self.start_time}>'


db.create_all()


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@ app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@ app.route('/venues')
def venues():
    # TODO: replace with real venues data.
    #  TODO: num_shows should be aggregated based on number of upcoming shows per venue.
    # data = [{
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "venues": [{
    #         "id": 1,
    #         "name": "The Musical Hop",
    #         "num_upcoming_shows": 0,
    #     }, {
    #         "id": 3,
    #         "name": "Park Square Live Music & Coffee",
    #         "num_upcoming_shows": 1,
    #     }]
    # }, {
    #     "city": "New York",
    #     "state": "NY",
    #     "venues": [{
    #             "id": 2,
    #             "name": "The Dueling Pianos Bar",
    #             "num_upcoming_shows": 0,
    #     }]
    # }]
    data = Venue.query.order_by(Venue.city).all()
    return render_template('pages/venues.html', areas=data)


@ app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

    # response = {
    #     "count": 2,
    #     "data": [{
    #         # "id": 2,
    #         # "name": "The Dueling Pianos Bar",
    #         # "num_upcoming_shows": 0,
    #     }]
    # }
    search = request.form.get('search_term', '')
    response = Venue.query.filter(Venue.name.ilike('%' + search + '%')).all()
    # print("RESPONSE: ", response)
    count = Venue.query.filter(Venue.name.ilike('%' + search + '%')).count()
    return render_template('pages/search_venues.html', results=response, total=count, search_term=search)


@ app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    data = {}
    try:
        # use to determine past & upcoming shows
        today = datetime.now()
        current_time = today.strftime("%Y-%m-%d %H:%M:%S")

        # retrieving & updating upcoming_shows_count & past_shows_count
        venue = Venue.query.filter(Venue.id == venue_id).first()
        total_upcoming_shows = Show.query.filter(
            Show.venue_id == venue_id, Show.start_time > current_time).count()

        total_past_shows = Show.query.filter(
            Show.venue_id == venue_id, Show.start_time < current_time).count()
        venue.upcoming_shows_count = total_upcoming_shows
        venue.past_shows_count = total_past_shows
        db.session.commit()

        result = Venue.query.filter(Venue.id == venue_id)
        for r in result:
            data = {
                "id": r.id,
                "name": r.name,
                "genres": r.genres,
                "address": r.address,
                "city": r.city,
                "state": r.state,
                "phone": r.phone,
                "website": r.website,
                "facebook_link": r.facebook_link,
                "seeking_talent": r.seeking_talent,
                "seeking_description": r.seeking_description,
                "image_link": r.image_link,
                "past_shows": [],
                "upcoming_shows": [],
                "past_shows_count": r.past_shows_count,
                "upcoming_shows_count": r.upcoming_shows_count,
            }
            for show, artist in db.session.query(Show, Artist).filter(Show.artist_id == Artist.id):
                if venue_id == show.venue_id:
                    if show.start_time < current_time:
                        past_show = {
                            "artist_id": artist.id,
                            "artist_name": artist.name,
                            "artist_image_link": artist.image_link,
                            "start_time": show.start_time
                        }
                        data['past_shows'].append(past_show)
                    else:
                        upcoming_show = {
                            "artist_id": artist.id,
                            "artist_name": artist.name,
                            "artist_image_link": artist.image_link,
                            "start_time": show.start_time
                        }
                        data['upcoming_shows'].append(upcoming_show)
    except:
        print(sys.exc_info())
        print('class Venue is None')
    finally:
        return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@ app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@ app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # !TODO: insert form data as a new Venue record in the db, instead
    # !TODO: modify data to be the data object returned from db insertion
    error = False
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        website = request.form['website']
        facebook_link = request.form['facebook_link']
        image_link = request.form['image_link']
        if request.form['seeking_talent'] == True:
            seeking_talent = True
            seeking_description = request.form['seeking_description']
        else:
            seeking_talent = False
            seeking_description = "Not currently seeking performance venues"
        venue = Venue(name=name, city=city, state=state,
                      address=address, phone=phone, genres=genres, website=website, facebook_link=facebook_link, image_link=image_link, seeking_talent=seeking_talent, seeking_description=seeking_description)
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        print(sys.exc_info())
        # !TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
        return render_template('pages/venues.html')
    else:
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        print(sys.exc_info())
        return render_template('pages/home.html')


@ app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
        return jsonify({'success': True})
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    # return None

#  Artists
#  ----------------------------------------------------------------


@ app.route('/artists')
def artists():
    # !TODO: replace with real data returned from querying the database
    # data = [{
    #     "id": 4,
    #     "name": "Guns N Petals",
    # }, {
    #     "id": 5,
    #     "name": "Matt Quevedo",
    # }, {
    #     "id": 6,
    #     "name": "The Wild Sax Band",
    # }]
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@ app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search = request.form.get('search_term', '')
    response = Artist.query.filter(Artist.name.ilike(f'%{search}%')).all()
    count = Artist.query.filter(Artist.name.ilike(f'%{search}%')).count()
    return render_template('pages/search_artists.html', results=response, total=count, search_term=search)


@ app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # !TODO: replace with real venue data from the venues table, using venue_id
    try:
        # determine past & upcoming shows
        today = datetime.now()
        current_time = today.strftime("%Y-%m-%d %H:%M:%S")

        # retrieving & updating -> past_shows_count & upcoming_shows_count
        artist = Artist.query.filter(Artist.id == artist_id).first()
        total_upcoming_shows = Show.query.filter(
            Show.artist_id == artist_id, Show.start_time > current_time).count()
        # print("total_upcoming_shows:", total_upcoming_shows)
        total_past_shows = Show.query.filter(
            Show.artist_id == artist_id, Show.start_time < current_time).count()
        # print("total_past_shows:", total_past_shows)
        artist.past_shows_count = total_past_shows
        artist.upcoming_shows_count = total_upcoming_shows
        db.session.commit()

        result = Artist.query.filter(Artist.id == artist_id)
        for r in result:
            data = {
                "id": r.id,
                "name": r.name,
                "genres": r.genres,
                "city": r.city,
                "state": r.state,
                "phone": r.phone,
                "seeking_venue": r.seeking_venue,
                "seeking_description": r.seeking_description,
                "image_link": r.image_link,
                "website": r.website,
                "facebook_link": r.facebook_link,
                "past_shows": [],
                "past_shows_count": r.past_shows_count,
                "upcoming_shows": [],
                "upcoming_shows_count": r.upcoming_shows_count
            }
            # displays shows
            for show, venue in db.session.query(Show, Venue).filter(Show.venue_id == Venue.id):
                if artist_id == show.artist_id:
                    if show.start_time < current_time:
                        past_show = {
                            "venue_id": venue.id,
                            "venue_name": venue.name,
                            "venue_image_link": venue.image_link,
                            "start_time": show.start_time
                        }
                        data['past_shows'].append(past_show)
                    else:
                        upcoming_show = {
                            "venue_id": venue.id,
                            "venue_name": venue.name,
                            "venue_image_link": venue.image_link,
                            "start_time": show.start_time
                        }
                        data['upcoming_shows'].append(upcoming_show)
    except:
        print('Cannot display artist information!')
        print(sys.exc_info())
    finally:
        return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    # !TODO: populate form with fields from artist with ID <artist_id>
    artist = Artist.query.get(artist_id)
    form = ArtistForm(request.form, obj=artist)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # !TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    try:
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.genres = form.genres.data
        artist.website = form.website.data
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        if form.seeking_venue.data:
            artist.seeking_venue = True
            artist.seeking_description = form.seeking_description.data
        if form.seeking_venue.data == "False":
            artist.seeking_venue = False
            artist.seeking_description = "Not currently seeking performance venues"
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' +
              form.name.data + ' could not be updated.')

    finally:
        db.session.close()
        flash('Info for ' + form.name.data + ' has been updated')
        return redirect(url_for('show_artist', artist_id=artist_id))


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    # !TODO: populate form with values from venue with ID <venue_id>
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # !TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    try:
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        # TODO: *figure out how to use enum
        venue.genres = form.genres.data
        venue.website = form.website.data
        venue.facebook_link = form.facebook_link.data
        venue.image_link = form.image_link.data
        if form.seeking_talent.data:
            venue.seeking_talent = True
            venue.seeking_description = form.seeking_description.data
        if form.seeking_talent.data == "False":
            venue.seeking_talent = False
            venue.seeking_description = "Not currently seeking performance venues"
        db.session.commit()
    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              form.name.data + ' could not be updated.')
        # print(artist.name)
    finally:
        db.session.close()
        flash('Info for ' + form.name.data + ' has been updated')
        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@ app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@ app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # !TODO: insert form data as a new Venue record in the db, instead
    # !TODO: modify data to be the data object returned from db insertion
    error = False
    try:
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        phone = request.form['phone']
        genres = request.form.getlist('genres')
        facebook_link = request.form['facebook_link']
        website = request.form['website']
        image_link = request.form['image_link']
        if request.form['seeking_venue'] == True:
            seeking_venue = True
            seeking_description = request.form['seeking_description']
        else:
            seeking_venue = False
            seeking_description = "Not currently seeking performance venues"

        artist = Artist(name=name, city=city, state=state,
                        phone=phone, facebook_link=facebook_link, website=website, image_link=image_link, seeking_description=seeking_description, seeking_venue=seeking_venue, genres=genres)
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        # !TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
        return render_template('pages/artists.html')
    else:
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        print(sys.exc_info())
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@ app.route('/shows')
def shows():
    # displays list of shows at /shows
    # !TODO: replace with real venues data.
    #  TODO: num_shows should be aggregated based on number of upcoming shows per venue.
    data = Show.query.order_by(Show.start_time).all()
    return render_template('pages/shows.html', shows=data)


@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # !TODO: insert form data as a new Show record in the db, instead
    error = False
    try:
        artist_id = request.form['artist_id']
        venue_id = request.form['venue_id']
        start_time = request.form['start_time']
        find_artist = Artist.query.filter(Artist.id == artist_id)
        for a in find_artist:
            artist_name = a.name
            artist_image_link = a.image_link
            break
        find_venue = Venue.query.filter(Venue.id == venue_id)
        for v in find_venue:
            venue_name = v.name
            break
        show = Show(artist_id=artist_id, venue_id=venue_id,
                    start_time=start_time, artist_name=artist_name, venue_name=venue_name, artist_image_link=artist_image_link)
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        # !TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        print(sys.exc_info())
        flash('An error occurred. Show could not be listed.')
        return render_template('pages/show.html')
    else:
        # on successful db insert, flash success
        flash('Show was successfully listed!')
        return render_template('pages/home.html')


@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
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
