let currentDeleteUser = null;

// 页面加载时获取用户信息和用户列表
document.addEventListener('DOMContentLoaded', function() {
    loadCurrentUser();
    loadUsers();
});

// 加载当前用户信息
function loadCurrentUser() {
    fetch('/auth/api/user/info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('currentUser').textContent = `欢迎，${data.username}`;
        })
        .catch(error => {
            console.error('加载用户信息失败:', error);
        });
}

// 加载用户列表
function loadUsers() {
    document.getElementById('usersLoading').style.display = 'block';
    document.getElementById('usersTable').style.display = 'none';

    fetch('/auth/api/users')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('usersTableBody');
            tbody.innerHTML = '';

            data.users.forEach(user => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${user.username}</td>
                    <td>
                        <span class="badge ${user.is_admin ? 'badge-admin' : 'badge-user'}">
                            ${user.is_admin ? '管理员' : '普通用户'}
                        </span>
                    </td>
                    <td>${formatDate(user.created_at)}</td>
                    <td>${user.last_login ? formatDate(user.last_login) : '从未登录'}</td>
                    <td>
                        ${!user.is_admin ? `<button class="btn btn-danger" onclick="deleteUser('${user.username}')">删除</button>` : ''}
                    </td>
                `;
                tbody.appendChild(row);
            });

            document.getElementById('usersLoading').style.display = 'none';
            document.getElementById('usersTable').style.display = 'table';
        })
        .catch(error => {
            console.error('加载用户列表失败:', error);
            showAlert('加载用户列表失败', 'danger');
            document.getElementById('usersLoading').style.display = 'none';
        });
}

// 创建新用户
function createUser() {
    fetch('/auth/api/users', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const userInfo = document.getElementById('newUserInfo');
            userInfo.innerHTML = `
                <p><strong>用户名:</strong> ${data.user.username}</p>
                <p><strong>密码:</strong> ${data.user.password}</p>
                <p><strong>创建时间:</strong> ${formatDate(data.user.created_at)}</p>
            `;
            document.getElementById('newUserModal').style.display = 'block';
            loadUsers(); // 刷新用户列表
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('创建用户失败:', error);
        showAlert('创建用户失败', 'danger');
    });
}

// 删除用户
function deleteUser(username) {
    currentDeleteUser = username;
    document.getElementById('deleteUsername').textContent = username;
    document.getElementById('deleteModal').style.display = 'block';
}

// 确认删除
function confirmDelete() {
    if (!currentDeleteUser) return;

    fetch(`/auth/api/users/${currentDeleteUser}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            loadUsers(); // 刷新用户列表
        } else {
            showAlert(data.message, 'danger');
        }
        closeModal('deleteModal');
    })
    .catch(error => {
        console.error('删除用户失败:', error);
        showAlert('删除用户失败', 'danger');
        closeModal('deleteModal');
    });
}

// 关闭模态框
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    if (modalId === 'deleteModal') {
        currentDeleteUser = null;
    }
}

// 显示提示信息
function showAlert(message, type) {
    const alertContainer = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    
    alertContainer.appendChild(alert);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (alert.parentNode) {
            alert.parentNode.removeChild(alert);
        }
    }, 3000);
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}