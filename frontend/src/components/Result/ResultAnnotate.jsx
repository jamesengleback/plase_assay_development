import { useState, useEffect, useContext } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faDeleteLeft,
  faComment,
  faSquareCheck,
  faHourglassStart,
  faLock,
  faLockOpen,
  faCheckCircle,
  faCircleXmark,
} from '@fortawesome/free-solid-svg-icons'
import { ResultContext } from './ResultContext';

export default function ResultAnnotate(props) {
  const [comments, setComments] = useState([])
  const [commentInput, setCommentInput] = useState([])
  const [locked, setLocked] = useState(props.locked)
  const [accepted, setAccepted] = useState(props.accepted)

  const resultContext = useContext(ResultContext);
  const id = resultContext.id

  // useEffect(() => {
  //   const handleKeyDown = (event) => {
  //     switch (event.key) {
  //       case 'Enter':
  //         event.preventDefault();
  //         console.warn('Enter')
  //         break;
  //     }
  //   };
  //
  //   window.addEventListener('keydown', handleKeyDown);
  //
  //   return () => {
  //     window.removeEventListener('keydown', handleKeyDown);
  //   };
  // }, [id]);

  useEffect(() => {
    setComments(props.annotations)
  }, [props]);

  // useEffect(() => {
  //   if (id) {
  //     fetch(`http://localhost:8008/comment/?result_id=${id}`)
  //       .then(res => res.json())
  //       .then(json => { setComments(json); })
  //       .catch(err => { console.error(err) })
  //   }
  // }, [props, id]);

  return (
    <div className='info-card'>
      <div className='row comment-submit'>
        <form action={(data) => {
          const form = new FormData()
          form.append('result_id', id)
          form.append('comment', data.get('comment'))
          fetch(`http://localhost:8008/comment/`,
            {
              method: 'POST',
              body: form
            }
          )
            .then(res => {
              if (!res.ok) {
                return res.json().then(errorJson => {
                  throw new Error(JSON.stringify(errorJson));
                });
              }
              return res.json();
            })
            .then(json => {
              setComments([json, ...comments]);
              setCommentInput('');
            })
            .catch(err => { console.error(err) })
        }}
          className='comment-submit'
        >
          {/* <label htmlFor='comment-input'> Comments </label> */}
          <input id='comment-input'
            name='comment'
            type='text'
            placeholder='Comment'
          />
        </form>
        <button
          style={{
            backgroundColor: locked ? 'var(--gruv-5)' : 'var(--gruv-28)'
          }}
          onClick={(event) => {
            const form = new FormData()
            const val = !locked
            setLocked(val);

            form.append('lock', val)
            fetch(`http://localhost:8008/result/${id}`,
              {
                method: 'PATCH',
                body: form
              }
            )
              .then(res => res.json())
              .then(json => { resultContext.setResult(json) })
              .catch(err => {
                console.error(err);
                setLocked(!locked);
              })
          }}
        >
          {
            (locked) ?
              <FontAwesomeIcon icon={faLock} />
              :
              <FontAwesomeIcon icon={faLockOpen} />
          }
        </button>
        <button
          style={{
            backgroundColor: accepted ? 'var(--gruv-5)' : 'var(--gruv-16)'
          }}
          onClick={(event) => {
            const form = new FormData()
            const val = !accepted
            setAccepted(val);
            form.append('accept', val)
            fetch(`http://localhost:8008/result/${id}`,
              {
                method: 'PATCH',
                body: form
              }
            )
              .then(res => res.json())
              .then(json => { resultContext.setResult(json) })
              .catch(err => {
                console.error(err);
                setAccepted(!val);
              })
          }}
        >
          {
            (accepted) ?
              <FontAwesomeIcon icon={faCheckCircle} />
              :
              <FontAwesomeIcon icon={faCircleXmark} />

          }
        </button>
      </div>
      <div className='comment-list'>
        {
          comments?.map((item, idx) => <div id={`comment-${idx}`} className='comment' key={idx}>
            <span>{item.comment}  </span>
            <button onClick={() => {

              fetch(`http://localhost:8008/comment/${item.id}`,
                { method: 'DELETE' }
              )
                .then(res => {
                  setComments(comments.filter(c => c.id !== item.id))
                  // document.getElementById(`comment-${idx}`).remove() 
                })
                .catch(err => { console.log(err) })
            }}>
              <FontAwesomeIcon icon={faDeleteLeft} />
            </button>
          </div>)
        }
      </div>
    </div >
  )
}
