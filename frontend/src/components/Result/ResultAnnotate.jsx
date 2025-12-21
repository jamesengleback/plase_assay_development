import { useState, useEffect, useContext } from 'react';
import PropTypes from 'prop-types';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faDeleteLeft,
  faLock,
  faLockOpen,
  faCheckCircle,
  faCircleXmark,
} from '@fortawesome/free-solid-svg-icons'
import { ResultContext } from './ResultContext';
import Spinner from '../utils/Spinner/Spinner';

export default function ResultAnnotate(props) {
  const [comments, setComments] = useState([])
  const [commentInput, setCommentInput] = useState('')
  const [locked, setLocked] = useState(props.locked)
  const [accepted, setAccepted] = useState(props.accepted)
  const [lockLoading, setLockLoading] = useState(false)
  const [acceptLoading, setAcceptLoading] = useState(false)
  const [error, setError] = useState('')

  const resultContext = useContext(ResultContext);
  const id = resultContext.id

  useEffect(() => {
    setComments(props.annotations)
    setAccepted(props.accepted)
    setLocked(props.locked)
  }, [props]);

  return (
    <div className='info-card'>
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'nowrap' }}>
      <form onSubmit={async (e) => {
        e.preventDefault();
        if (!commentInput.trim()) {
          setError('Comment cannot be empty');
          return;
        }
        setError('');
        const form = new FormData()
        form.append('result_id', id)
        form.append('comment', commentInput)
        try {
          const res = await fetch(`http://localhost:8008/comment/`, {
            method: 'POST',
            body: form
          });
          if (!res.ok) {
            const errorJson = await res.json();
            throw new Error(JSON.stringify(errorJson));
          }
          const json = await res.json();
          setComments([json, ...comments]);
          setCommentInput('');
        } catch (err) {
          console.error(err);
          try {
            const errorDetail = JSON.parse(err.message).detail;
            setError(errorDetail || 'Failed to add comment');
          } catch {
            setError('Failed to add comment');
          }
        }
      }}
        style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
      >
        <input id='comment-input'
          name='comment'
          type='text'
          value={commentInput}
          onChange={(e) => setCommentInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              document.getElementById('comment-input').form.requestSubmit();
            }
          }}
          style={{ height: '2em' }}
        />
      </form>
      {error && <div style={{ color: 'var(--gruv-26)', marginTop: '5px' }}>{error}</div>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
        <button
          disabled={lockLoading}
          style={{
            backgroundColor: locked ? 'var(--gruv-5)' : 'var(--gruv-28)',
            height: '2em',
            width: '140px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-start',
            textAlign: 'left'
          }}
          onClick={async () => {
            setError('');
            setLockLoading(true);
            const val = !locked;
            setLocked(val);
            const form = new FormData();
            form.append('lock', val);
            try {
              const res = await fetch(`http://localhost:8008/result/${id}`, {
                method: 'PATCH',
                body: form
              });
              const json = await res.json();
              resultContext.setResult(json);
            } catch (err) {
              console.error(err);
              setLocked(!val);
              setError('Failed to update lock status');
            } finally {
              setLockLoading(false);
            }
          }}
        >
          {lockLoading ? <Spinner /> : (
            <>
              <FontAwesomeIcon icon={locked ? faLock : faLockOpen} style={{ marginRight: '5px' }} />
              <span>{locked ? 'Locked' : 'Unlocked'}</span>
            </>
          )}
        </button>
        <button
          disabled={acceptLoading}
          style={{
            backgroundColor: accepted ? 'var(--gruv-5)' : 'var(--gruv-16)',
            height: '2em',
            width: '140px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-start',
            textAlign: 'left'
          }}
          onClick={async () => {
            setError('');
            setAcceptLoading(true);
            const val = !accepted;
            setAccepted(val);
            const form = new FormData();
            form.append('accept', val);
            try {
              const res = await fetch(`http://localhost:8008/result/${id}`, {
                method: 'PATCH',
                body: form
              });
              const json = await res.json();
              resultContext.setResult(json);
            } catch (err) {
              console.error(err);
              setAccepted(!val);
              setError('Failed to update accept status');
            } finally {
              setAcceptLoading(false);
            }
          }}
        >
          {acceptLoading ? <Spinner /> : (
            <>
              <FontAwesomeIcon icon={accepted ? faCheckCircle : faCircleXmark} style={{ marginRight: '5px' }} />
              <span>{accepted ? 'Accepted' : 'Not Accepted'}</span>
            </>
          )}
        </button>
      </div>
    </div>
    <hr style={{ border: '1px solid var(--gruv-3)', margin: '10px 0' }} />
    <div className='comment-list'>
        {
          comments?.map((item, idx) => <div id={`comment-${idx}`} className='comment' key={idx}>
            <span>{item.comment}  </span>
            <button style={{ color: 'var(--gruv-26)', backgroundColor: 'var(--gruv-2)' }} onClick={() => {
              fetch(`http://localhost:8008/comment/${item.id}`,
                { method: 'DELETE' }
              )
                .then(() => {
                  setComments(comments.filter(c => c.id !== item.id))
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

ResultAnnotate.propTypes = {
  annotations: PropTypes.array,
  locked: PropTypes.bool,
  accepted: PropTypes.bool,
}
