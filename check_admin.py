from usuarios.models import Usuario
from django.contrib.auth import authenticate

# Verificar usuário admin
user = Usuario.objects.filter(username='admin').first()

if user:
    print(f"✅ Usuário admin encontrado:")
    print(f"   - ID: {user.id}")
    print(f"   - Username: {user.username}")
    print(f"   - Email: {user.email}")
    print(f"   - Ativo: {user.is_active}")
    print(f"   - Staff: {user.is_staff}")
    print(f"   - Superuser: {user.is_superuser}")
    print(f"   - Empresa ID: {user.empresa_id}")
    
    # Verificar se a senha está definida
    if user.password:
        print(f"   - Senha definida: ✅")
    else:
        print(f"   - Senha definida: ❌")
        
    # Testar autenticação com senha comum
    test_passwords = ['admin', '123456', 'password', 'admin123', '1234', 'escalator', 'Escalator123']
    
    print(f"\n🔍 Testando senhas comuns:")
    senha_encontrada = False
    for pwd in test_passwords:
        auth_user = authenticate(username='admin', password=pwd)
        if auth_user:
            print(f"   ✅ Senha '{pwd}' funciona!")
            senha_encontrada = True
            break
        else:
            print(f"   ❌ Senha '{pwd}' não funciona")
    
    if not senha_encontrada:
        print(f"\n⚠️  Nenhuma senha comum funcionou. Pode ser necessário resetar a senha.")
    
else:
    print("❌ Usuário admin não encontrado!")
    
    # Listar todos os usuários
    print("\n📋 Usuários existentes:")
    for u in Usuario.objects.all():
        print(f"   - {u.username} (ID: {u.id}, Ativo: {u.is_active}, Empresa: {u.empresa_id})")
        
    # Verificar se existe algum superuser
    superusers = Usuario.objects.filter(is_superuser=True)
    if superusers.exists():
        print(f"\n👑 Superusuários encontrados:")
        for su in superusers:
            print(f"   - {su.username} (ID: {su.id})")
    else:
        print(f"\n⚠️  Nenhum superusuário encontrado!")