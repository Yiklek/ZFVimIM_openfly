let s:repoPath=expand('<sfile>:p:h:h')
function! s:dbInit()
    let name = 'openfly'
    let repoPath = s:repoPath
    let dbFile = '/misc/'.name.'.txt'
    let dbCountFile = '/misc/'.name.'_count.txt'

    let db = ZFVimIM_dbInit({
                \   'name' : name,
                \ })
    call ZFVimIM_cloudRegister({
                \   'mode':'local',
                \   'repoPath' : repoPath,
                \   'dbFile' : dbFile,
                \   'dbId' : db['dbId'],
                \ })
endfunction

augroup ZFVimIM_openfly_augroup
    autocmd!
    autocmd User ZFVimIM_event_OnDbInit call s:dbInit()
augroup END

