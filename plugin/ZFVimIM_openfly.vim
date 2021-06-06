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
                \   'repoPath' : repoPath,
                \   'dbFile' : dbFile,
                \   'dbCountFile' : dbCountFile,
                \   'gitUserEmail' : get(g:, 'ZFVimIM_'.name.'_gitUserEmail', get(g:, 'zf_git_user_email', '')),
                \   'gitUserName' : get(g:, 'ZFVimIM_'.name.'_gitUserName', get(g:, 'zf_git_user_name', '')),
                \   'gitUserToken' : get(g:, 'ZFVimIM_'.name.'_gitUserToken', get(g:, 'zf_git_user_token', '')),
                \   'dbId' : db['dbId'],
                \ })
endfunction

augroup ZFVimIM_openfly_augroup
    autocmd!
    autocmd User ZFVimIM_event_OnDbInit call s:dbInit()
augroup END

