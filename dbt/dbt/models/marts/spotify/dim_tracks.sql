select
    t.track_id,
    t.spotify_track_id,
    t.track_name,
    t.track_uri,
    t.duration_ms,
    t.explicit,
    t.popularity,
    ar.artist_id,
    ar.spotify_artist_id,
    ar.artist_name,
    ar.artist_uri,
    al.album_id,
    al.spotify_album_id,
    al.album_name,
    al.album_uri,
    al.release_date,
    al.total_tracks
from {{ ref('track') }} t
left join {{ ref('artist') }} ar on t.artist_id = ar.spotify_artist_id
left join {{ ref('album') }} al on t.album_id = al.spotify_album_id
